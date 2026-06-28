import asyncio
import logging
import json
import os
from typing import Optional
from fastapi import Depends, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from ...db import sm
from .. import router as app
from ..jwt import get_user, user_required
from ..users.models import User
from ..ai.openai_api import (
    reply_text_default,
    get_chat_ai_model,
    resolve_conversation_model_type,
)
from .forms import (
    ConversationFilterForm,
    ConversationForm,
    MessageForm,
    ScriptFilterForm,
    ScriptForm,
    ScriptUpdateForm,
    ChatStreamForm,
    ScriptGenerateForm,
    VoiceMessageForm,
    VoiceStreamForm,
    MessageConfirmForm,
    MessageRetryForm,
    # 研究相关表单
    ScriptResearchFilterForm,
    StartResearchForm,
    ResearchChatForm,
    UpdateResearchDataForm,
    CompleteResearchForm,
    ArchiveResearchForm,
    ScriptMediaForm,
)
from .models import Conversation, Message, Script, UserStyleProfile, ScriptResearch, ScriptMedia
from .constants import (
    ConversationStatus,
    ConversationType,
    ScriptStatus, 
    MessageRole, 
    TranscriptionStatus, 
    RefinementStatus,
    ResearchStatus,
    ScriptMediaStatus,
)
from .prompts import (
    get_conversation_system_prompt,
    get_script_generation_prompt,
    get_script_extraction_prompt,
    build_script_reference_block,
    SCRIPT_REFERENCE_USAGE_HINT,
    # 研究相关prompts
    get_research_system_prompt,
    get_research_initial_message,
    get_research_analysis_prompt,
    get_research_summary_prompt,
)
from ..media.models import MediaModel
from ...config import config
from .whisper_service import append_webm_segment

logger = logging.getLogger(__name__)


def _verify_codex_token(x_codex_token: Optional[str]):
    expected = config.CREATOR_CODEX_TOKEN
    if not expected:
        raise HTTPException(status_code=500, detail='CREATOR_CODEX_TOKEN 未配置')
    if x_codex_token != expected:
        raise HTTPException(status_code=401, detail='Codex token 无效')


def _resolve_codex_user(db: Session, user_id: Optional[int]) -> User:
    target_user_id = user_id if user_id is not None else config.CREATOR_CODEX_USER_ID

    if target_user_id is not None:
        user = db.query(User).filter(User.id == target_user_id).first()
    else:
        user = db.query(User).order_by(User.id.asc()).first()

    if not user:
        raise HTTPException(status_code=404, detail='未找到可用于 Codex 的 Creator 用户')
    return user


def _verify_message_access(db: Session, message_id: int, user_id: int):
    """校验消息存在且属于当前用户，返回 Message。"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail='消息不存在')

    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == user_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=403, detail='无权访问此消息')
    return message


def _build_message_processing_status(message: Message) -> dict:
    """构建语音处理状态（轮询 / SSE 共用）。"""
    stream_chunks_data = message.stream_chunks or {}
    chunks_list = stream_chunks_data.get('chunks', [])
    partial_text = ''.join(
        c.get('text', '') for c in sorted(chunks_list, key=lambda x: x.get('index', 0))
    ) if chunks_list else None
    transcription_status = message.transcription_status
    transcription_error = message.transcription_error

    # Whisper 冷启动/未就绪属于可恢复状态，尤其已有 partial 时不应在前端展示为失败。
    if transcription_error and 'Whisper 服务未正确初始化' in transcription_error:
        transcription_status = TranscriptionStatus.PROCESSING.value
        transcription_error = None

    return {
        'message_id': message.id,
        'transcription': {
            'status': TranscriptionStatus.init(transcription_status).dump() if transcription_status else None,
            'raw_text': message.raw_transcription,
            'segments': message.transcription_segments,
            'error': transcription_error,
            'audio_duration': message.audio_duration,
            'partial_text': partial_text,
            'processed_chunks': message.stream_chunk_count or 0,
        },
        'refinement': {
            'status': RefinementStatus.init(message.refinement_status).dump() if message.refinement_status else None,
            'result': message.refinement_result,
            'refined_content': message.refined_content,
            'error': message.refinement_error,
        },
        'user_confirmed': bool(message.user_confirmed) if message.user_confirmed is not None else False,
    }


# ==================== 会话相关接口 ====================

@app.get('/web/conversations')
@user_required
async def get_conversations(
    form: ConversationFilterForm = Depends(),
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取会话列表"""
    query = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    )

    # 关键词过滤
    if form.keyword:
        query = query.filter(
            Conversation.title.ilike(f'%{form.keyword}%')
        )

    # 状态过滤
    if form.status:
        query = query.filter(Conversation.status == form.status)

    # 排序
    query = query.order_by(desc(Conversation.created_at))

    # 使用分页方法
    return Conversation.paginated_dump(query=query, form=form)


@app.post('/web/conversations')
@user_required
async def create_conversation(
    form: ConversationForm,
    current_user: User = Depends(get_user)
):
    """创建新会话"""
    with sm.transaction_scope() as sa:
        conversation = Conversation.create(
            sa,
            user_id=current_user.id,
            title=form.title,
            topic=form.topic,
            status=ConversationStatus.IN_PROGRESS
        )
        # ProfileMixin属性单独设置
        conversation.message_count = 0
        conversation.total_tokens = 0
        conversation.context_summary = {}
        
        # ✅ 在 session 关闭前调用 dump()
        result = conversation.dump()

    return dict(success=True, data=result)


@app.get('/web/conversations/{conversation_id}')
@user_required
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取单个会话详情"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    return dict(success=True, data=conversation.dump())


@app.delete('/web/conversations/{conversation_id}')
@user_required
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """删除会话（级联删除关联的消息和脚本）"""
    # 先在查询 session 中验证会话是否存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # ✅ 正确：在新 session 中重新获取对象，先删除关联数据再删除会话
    with sm.transaction_scope() as sa:
        # 1. 删除关联的消息
        sa.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete(synchronize_session=False)
        
        # 2. 删除关联的脚本
        sa.query(Script).filter(
            Script.conversation_id == conversation_id
        ).delete(synchronize_session=False)
        
        # 3. 删除会话本身
        conv = Conversation.get_or_404(sa, conversation_id)
        sa.delete(conv)
        
        logger.info(f"删除会话 {conversation_id} 及其关联数据")

    return dict(success=True, message='删除成功')


@app.post('/web/conversations/{conversation_id}/generate-title')
@user_required
async def generate_conversation_title(
    conversation_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    根据第一条用户消息自动生成对话标题
    
    逻辑：
    1. 如果第一条消息≤5个字，直接使用原文作为标题
    2. 如果>5个字，调用AI生成简短标题（5-15字）
    """
    # 1. 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 2. 获取第一条用户消息
    first_user_message = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.role == 'user'
    ).order_by(Message.created_at).first()

    if not first_user_message:
        raise HTTPException(status_code=400, detail='对话中没有用户消息')

    # 3. 智能判断：短消息直接使用，长消息AI总结
    message_content = first_user_message.content.strip()
    message_length = len(message_content)
    
    if message_length <= 5:
        # 短消息直接使用原文作为标题
        generated_title = message_content
        logger.info(f"短消息直接作为标题: {generated_title}")
    else:
        # 长消息调用AI生成标题
        try:
            from .prompts import get_conversation_title_prompt
            title_prompt = get_conversation_title_prompt(message_content)

            # 构建简单的消息列表
            messages = [
                {
                    "role": "user",
                    "content": title_prompt
                }
            ]
            
            # 调用AI（非流式，直接获取结果）
            generated_title = await reply_text_default(messages, current_user)
            
            # 清理标题（去除引号、标点、换行等）
            generated_title = generated_title.strip().strip('"\'""''。，！？、：；\n\r')
            
            # 严格限制长度（5-15字）
            if len(generated_title) < 5:
                # 如果AI生成的太短，使用原消息的前15字
                generated_title = message_content[:15]
            elif len(generated_title) > 15:
                generated_title = generated_title[:15]
            
            logger.info(f"AI生成标题: {generated_title}")
            
        except Exception as e:
            logger.error(f"AI生成标题失败: {str(e)}")
            # AI失败时降级处理：使用原消息的前15字
            generated_title = message_content[:15]
            logger.info(f"降级使用原消息前15字: {generated_title}")

    # 4. 更新对话标题
    try:
        with sm.transaction_scope() as sa:
            conv = Conversation.get_or_404(sa, conversation_id)
            conv.title = generated_title
            conv.updated_at = datetime.utcnow()
            
            result = conv.dump()
        
        return dict(success=True, data=result)
        
    except Exception as e:
        logger.error(f"更新标题失败: {str(e)}")
        raise HTTPException(status_code=500, detail='标题更新失败')


# ==================== 消息相关接口 ====================

@app.get('/web/conversations/{conversation_id}/messages')
@user_required
async def get_messages(
    conversation_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取会话的所有消息"""
    # 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    return dict(
        success=True,
        data=[msg.dump() for msg in messages]
    )


@app.post('/web/messages')
@user_required
async def create_message(
    form: MessageForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """创建新消息"""
    # 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == form.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    with sm.transaction_scope() as sa:
        message = Message.create(
            sa,
            conversation_id=form.conversation_id,
            role=form.role,
            content=form.content
        )
        # ProfileMixin属性单独设置
        if form.audio_url:
            message.audio_url = form.audio_url
        if form.audio_duration:
            message.audio_duration = form.audio_duration
        
        # ✅ 在 session 关闭前调用 dump()
        result = message.dump()

    return dict(success=True, data=result)


@app.post('/web/conversations/{conversation_id}/messages/voice')
@user_required
async def create_voice_message(
    conversation_id: int,
    form: VoiceMessageForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    创建语音消息
    
    流程：
    1. 验证会话和音频文件
    2. 创建Message记录（状态为转写中）
    3. 触发后台任务：转写 → 整理
    4. 立即返回消息ID和任务状态
    """
    # 1. 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 2. 验证音频文件是否存在
    media = db.query(MediaModel).filter(
        MediaModel.id == form.audio_media_id
    ).first()

    if not media:
        raise HTTPException(status_code=404, detail='音频文件不存在')

    # 3. 创建语音消息记录
    with sm.transaction_scope() as sa:
        message = Message.create(
            sa,
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=''  # 初始为空，等待转写完成后填充
        )
        
        # 设置 ProfileMixin 属性
        message.audio_media_id = form.audio_media_id
        message.transcription_status = TranscriptionStatus.PENDING.value
        message.refinement_status = RefinementStatus.PENDING.value
        message.user_confirmed = 0
        
        # ✅ 在 session 关闭前调用 dump()
        result = message.dump()
    
    # 4. 触发后台转写任务（异步）
    # TODO: 在 tasks.py 中实现 transcribe_audio_task
    from .tasks import transcribe_audio_task
    transcribe_audio_task(result['id'])
    
    return dict(
        success=True,
        data=result,
        message='语音消息创建成功，正在转写中...'
    )


@app.post('/web/conversations/{conversation_id}/voice-stream')
@user_required
async def create_voice_stream_chunk(
    conversation_id: int,
    form: VoiceStreamForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    流式语音分块上传接口

    前端定期上传**本段**切片；首块建立主录音，后续块追加到主文件后转写新增时段。
    - 首块（chunk_index=0, message_id=None）：创建 Message 并返回 message_id
    - 后续块：携带 message_id，服务端追加切片到主录音
    - 最终块（is_final=True）：触发文本合并 + 整理任务
    - 中途切片应始终 is_final=False；仅收尾块 is_final=True
    """
    # 1. 验证会话归属
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 2. 验证音频文件存在
    media = db.query(MediaModel).filter(
        MediaModel.id == form.audio_media_id
    ).first()

    if not media:
        raise HTTPException(status_code=404, detail='音频文件不存在')

    # 3. 首块：创建 Message
    if form.chunk_index == 0 and form.message_id is None:
        with sm.transaction_scope() as sa:
            message = Message.create(
                sa,
                conversation_id=conversation_id,
                role=MessageRole.USER.value,
                content=''
            )
            message.audio_media_id = form.audio_media_id
            message.transcription_status = TranscriptionStatus.PROCESSING.value
            message.refinement_status = RefinementStatus.PENDING.value
            message.user_confirmed = 0
            message.stream_chunks = {'chunks': [], 'last_end_time': 0.0}
            message.stream_chunk_count = 0
            result = message.dump()

        message_id = result['id']
    else:
        # 后续块：验证 message 归属
        if not form.message_id:
            raise HTTPException(status_code=400, detail='非首块请求必须提供 message_id')

        msg = db.query(Message).filter(Message.id == form.message_id).first()
        if not msg:
            raise HTTPException(status_code=404, detail='消息不存在')

        # 验证消息归属（通过会话）
        msg_conv = db.query(Conversation).filter(
            Conversation.id == msg.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not msg_conv:
            raise HTTPException(status_code=403, detail='无权访问此消息')

        message_id = form.message_id

    # 3.1 后续块：将本段切片追加到主录音文件
    transcribe_media_id = form.audio_media_id
    if form.chunk_index > 0:
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            master_media_id = message.audio_media_id
            if not master_media_id:
                raise HTTPException(status_code=400, detail='缺少主录音文件，请先上传首块')

            master = MediaModel.get_or_404(sa, master_media_id)
            chunk = MediaModel.get_or_404(sa, form.audio_media_id)
            master_path = os.path.join(config.UPLOADS_DEFAULT_DEST, master.filename)
            chunk_path = os.path.join(config.UPLOADS_DEFAULT_DEST, chunk.filename)
            try:
                append_webm_segment(master_path, chunk_path)
            except (FileNotFoundError, ValueError) as e:
                raise HTTPException(status_code=400, detail=str(e))
            transcribe_media_id = master_media_id

    # 取消/删除后不再调度转写
    message_exists = db.query(Message.id).filter(Message.id == message_id).first()
    if not message_exists:
        raise HTTPException(status_code=404, detail='消息不存在或已取消')

    # 4. 触发分块转写（默认 API 进程内，复用已预热的 Whisper）
    from .tasks import dispatch_transcribe_voice_chunk
    dispatch_result = dispatch_transcribe_voice_chunk(
        message_id,
        transcribe_media_id,
        form.chunk_index,
        form.is_final
    )
    logger.info(
        '语音分块转写已分发: message_id=%s, media_id=%s, chunk_index=%s, '
        'is_final=%s, mode=%s',
        message_id,
        transcribe_media_id,
        form.chunk_index,
        form.is_final,
        dispatch_result,
    )

    return dict(
        success=True,
        data={
            'message_id': message_id,
            'chunk_index': form.chunk_index,
            'is_final': form.is_final
        },
        message='分块已接收，正在转写...'
    )


@app.get('/web/messages/{message_id}/processing-status')
@user_required
async def get_message_processing_status(
    message_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    查询消息处理状态（轮询接口）
    
    返回转写和整理的进度状态
    """
    message = _verify_message_access(db, message_id, current_user.id)
    return dict(success=True, data=_build_message_processing_status(message))


@app.get('/web/messages/{message_id}/processing-status/stream')
@user_required
async def stream_message_processing_status(
    message_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    语音处理状态 SSE 推送（有更新时推送，完成/失败后结束）
    """
    _verify_message_access(db, message_id, current_user.id)

    async def event_generator():
        last_signature = None
        idle_rounds = 0
        max_idle_rounds = 120  # 0.5s * 120 ≈ 60s 无变化后结束

        while idle_rounds < max_idle_rounds:
            with sm.transaction_scope() as sa:
                message = Message.get_or_404(sa, message_id)
                status_data = _build_message_processing_status(message)

            trans = status_data.get('transcription') or {}
            trans_status = (trans.get('status') or {}).get('name')
            signature = (
                trans.get('partial_text'),
                trans.get('processed_chunks'),
                trans_status,
                trans.get('raw_text'),
                trans.get('error'),
            )

            if signature != last_signature:
                payload = json.dumps({'success': True, 'data': status_data}, ensure_ascii=False)
                yield f'data: {payload}\n\n'
                last_signature = signature
                idle_rounds = 0
            else:
                idle_rounds += 1

            if trans_status in ('COMPLETED', 'FAILED'):
                yield f'data: {json.dumps({"done": True}, ensure_ascii=False)}\n\n'
                return

            await asyncio.sleep(0.5)

        yield f'data: {json.dumps({"done": True}, ensure_ascii=False)}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@app.post('/web/messages/{message_id}/confirm')
@user_required
async def confirm_message_content(
    message_id: int,
    form: MessageConfirmForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    用户确认或修改整理后的内容
    
    流程：
    1. 更新消息内容为用户确认/修改后的内容
    2. 标记为已确认
    3. 如果 send_to_ai=True，触发AI对话
    """
    # 获取消息
    message = db.query(Message).filter(
        Message.id == message_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail='消息不存在')

    # 验证消息所属会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=403, detail='无权访问此消息')

    # 更新消息内容
    with sm.transaction_scope() as sa:
        msg = Message.get_or_404(sa, message_id)
        msg.content = form.content
        msg.user_confirmed = 1
        msg.updated_at = datetime.utcnow()
        
        # 更新会话统计
        conv = Conversation.get_or_404(sa, message.conversation_id)
        conv.message_count = (conv.message_count or 0) + 1
        conv.updated_at = datetime.utcnow()
        
        # ✅ 在 session 关闭前调用 dump()
        result = msg.dump()
    
    response_data = {'message': result}
    
    # 如果需要发送给AI
    if form.send_to_ai:
        # TODO: 触发AI对话任务或直接调用AI
        # 这里可以复用现有的 chat_stream 逻辑
        response_data['ai_triggered'] = True
        response_data['message_text'] = '已发送给AI，请等待回复'
    
    return dict(success=True, data=response_data)


@app.delete('/web/messages/{message_id}')
@user_required
async def delete_draft_message(
    message_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user),
):
    """删除未确认的语音草稿消息（取消/重录时清理空消息）。"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return dict(success=True, data={'deleted_id': message_id, 'already_deleted': True})

    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=403, detail='无权访问此消息')

    if message.user_confirmed:
        raise HTTPException(status_code=400, detail='已确认的消息不能删除')

    content = (message.content or '').strip()
    has_audio = bool(message.audio_media_id)
    if content and not has_audio:
        raise HTTPException(status_code=400, detail='仅可删除未确认的语音草稿')

    with sm.transaction_scope() as sa:
        msg = Message.get_or_404(sa, message_id)
        sa.delete(msg)

    return dict(success=True, data={'deleted_id': message_id})


@app.post('/web/messages/{message_id}/voice-finalize')
@user_required
async def finalize_voice_message(
    message_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user),
):
    """流式录音正常结束但无有效尾片时，合并已上传分块的转写结果。"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail='消息不存在')

    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=403, detail='无权访问此消息')

    from .tasks import _finalize_voice_transcription
    _finalize_voice_transcription(message_id)

    return dict(success=True, data={'message_id': message_id})


@app.post('/web/messages/{message_id}/retry')
@user_required
async def retry_message_processing(
    message_id: int,
    form: MessageRetryForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    重试失败的转写或整理任务
    
    参数：
    - retry_type: 'transcription' 或 'refinement'
    """
    # 获取消息
    message = db.query(Message).filter(
        Message.id == message_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail='消息不存在')

    # 验证消息所属会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=403, detail='无权访问此消息')

    # 更新状态并触发重试
    with sm.transaction_scope() as sa:
        msg = Message.get_or_404(sa, message_id)
        
        if form.retry_type == 'transcription':
            # 重置转写状态
            msg.transcription_status = TranscriptionStatus.PENDING.value
            msg.transcription_error = None
            
            # 触发转写任务
            from .tasks import transcribe_audio_task
            transcribe_audio_task(message_id)
            
            retry_message = '转写任务已重新触发'
            
        elif form.retry_type == 'refinement':
            # 重置整理状态
            msg.refinement_status = RefinementStatus.PENDING.value
            msg.refinement_error = None
            
            # 触发整理任务
            from .tasks import refine_transcription_task
            refine_transcription_task(message_id)
            
            retry_message = '整理任务已重新触发'
            
        else:
            raise HTTPException(status_code=400, detail='无效的重试类型')
        
        # ✅ 在 session 关闭前调用 dump()
        result = msg.dump()
    
    return dict(
        success=True,
        data=result,
        message=retry_message
    )


# ==================== 脚本相关接口 ====================

@app.get('/web/scripts')
@user_required
async def get_scripts(
    form: ScriptFilterForm = Depends(),
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取脚本列表"""
    query = db.query(Script).filter(
        Script.user_id == current_user.id
    )

    # 关键词过滤
    if form.keyword:
        query = query.filter(
            Script.title.ilike(f'%{form.keyword}%')
        )

    # 状态过滤
    if form.status:
        query = query.filter(Script.status == form.status)

    # 格式类型过滤
    if form.format_type:
        query = query.filter(Script.format_type == form.format_type)

    # 会话过滤
    if form.conversation_id:
        query = query.filter(Script.conversation_id == form.conversation_id)

    # 排序
    query = query.order_by(desc(Script.created_at))

    return Script.paginated_dump(query=query, form=form)


@app.post('/web/scripts')
@user_required
async def create_script(
    form: ScriptForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """创建新脚本"""
    # 如果有conversation_id,验证会话是否属于当前用户
    if form.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == form.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail='会话不存在')

    with sm.transaction_scope() as sa:
        script = Script.create(
            sa,
            user_id=current_user.id,
            conversation_id=form.conversation_id,
            title=form.title,
            content=form.content,
            format_type=form.format_type,
            status=ScriptStatus.DRAFT
        )
        # ProfileMixin属性单独设置
        script.subtitle = form.subtitle
        script.word_count = len(form.content)
        
        # ✅ 在 session 关闭前调用 dump()
        result = script.dump()

    return dict(success=True, data=result)


@app.get('/web/scripts/{script_id}')
@user_required
async def get_script(
    script_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取单个脚本详情"""
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()

    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    return dict(success=True, data=script.dump())


@app.put('/web/scripts/{script_id}')
@user_required
async def update_script(
    script_id: int,
    form: ScriptUpdateForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """更新脚本"""
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()

    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    with sm.transaction_scope() as sa:
        # 在新session中重新获取对象
        script = Script.get_or_404(sa, script_id)

        # 更新字段
        if form.title is not None:
            script.title = form.title
        if form.content is not None:
            script.content = form.content
            script.word_count = len(form.content)
        if form.status is not None:
            script.status = form.status
        if form.quality_score is not None:
            script.quality_score = form.quality_score
        
        # ✅ 在 session 关闭前调用 dump()
        result = script.dump()

    return dict(success=True, data=result)


@app.delete('/web/scripts/{script_id}')
@user_required
async def delete_script(
    script_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """删除脚本"""
    # 先在查询 session 中验证脚本是否存在且属于当前用户
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()

    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    # ✅ 正确：在新 session 中重新获取对象再删除
    with sm.transaction_scope() as sa:
        script_to_delete = Script.get_or_404(sa, script_id)
        # 再次验证用户权限（安全措施）
        if script_to_delete.user_id != current_user.id:
            raise HTTPException(status_code=403, detail='无权删除此脚本')
        sa.delete(script_to_delete)
        logger.info(f"删除脚本 {script_id}")

    return dict(success=True, message='删除成功')


@app.post('/web/conversations/{conversation_id}/extract-script')
@user_required
async def extract_script_from_conversation(
    conversation_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """
    从对话中提取脚本内容
    
    流程：
    1. 验证会话是否属于当前用户
    2. 获取对话的所有消息
    3. 检查是否有AI回复（至少要有对话）
    4. 调用AI提取脚本（使用提取提示词）
    5. 解析返回的JSON
    6. 验证是否有脚本内容
    7. 返回结构化数据
    """
    # 1. 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 2. 获取对话的所有消息
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    if not messages or len(messages) == 0:
        raise HTTPException(
            status_code=400, 
            detail='对话中没有消息记录，请先与AI讨论您的创意需求'
        )

    # 3. 检查是否有AI回复
    has_ai_reply = any(msg.role == 'assistant' for msg in messages)
    if not has_ai_reply:
        raise HTTPException(
            status_code=400,
            detail='对话中没有AI回复，请先与AI进行讨论'
        )

    # 4. 构建消息列表供AI分析
    conversation_messages = []
    for msg in messages:
        conversation_messages.append({
            'role': msg.role,
            'content': msg.content
        })

    # 5. 调用AI提取脚本
    try:
        # 生成提取提示词
        extraction_prompt = get_script_extraction_prompt(conversation_messages)
        
        # 构建AI消息
        ai_messages = [
            {
                "role": "user",
                "content": extraction_prompt
            }
        ]
        
        # 默认 DeepSeek；脚本较长时使用 8000 tokens
        ai_response = await reply_text_default(
            ai_messages, current_user, max_tokens=8000
        )
        
        logger.info(f"AI提取响应: {ai_response}")
        
        # 6. 解析JSON响应
        # 尝试提取JSON（AI可能在markdown代码块中返回）
        import re
        
        # 方法1: 尝试提取markdown代码块中的JSON（使用贪婪匹配）
        json_match = re.search(r'```json\s*(\{.*\})\s*```', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 方法2: 尝试提取markdown代码块中的JSON（没有闭合标记的情况）
            json_match = re.search(r'```json\s*(\{.*)', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # 尝试找到最后一个完整的 }
                last_brace = json_str.rfind('}')
                if last_brace > 0:
                    json_str = json_str[:last_brace + 1]
            else:
                # 方法3: 尝试直接找到第一个 { 和最后一个 }
                first_brace = ai_response.find('{')
                last_brace = ai_response.rfind('}')
                if first_brace >= 0 and last_brace > first_brace:
                    json_str = ai_response[first_brace:last_brace + 1]
                else:
                    # 方法4: 直接使用原始响应
                    json_str = ai_response.strip()
        
        # 清理可能的markdown标记
        json_str = json_str.strip()
        if json_str.startswith('```json'):
            json_str = json_str[7:].strip()
        if json_str.startswith('```'):
            json_str = json_str[3:].strip()
        if json_str.endswith('```'):
            json_str = json_str[:-3].strip()
        
        # 尝试解析JSON，如果失败则尝试修复被截断的字符串
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 如果是因为字符串未闭合导致的错误，尝试修复
            error_msg = str(e)
            if 'Unterminated string' in error_msg or 'Expecting' in error_msg:
                logger.warning(f"检测到JSON可能被截断，尝试修复: {error_msg}")
                try:
                    # 方法：找到最后一个完整的引号（非转义的），然后闭合JSON
                    # 从后往前查找，找到第一个非转义的引号
                    fixed_json = None
                    for i in range(len(json_str) - 1, -1, -1):
                        if json_str[i] == '"':
                            # 检查是否是转义的引号
                            escape_count = 0
                            j = i - 1
                            while j >= 0 and json_str[j] == '\\':
                                escape_count += 1
                                j -= 1
                            # 如果是偶数个转义符（包括0），说明是真正的结束引号
                            if escape_count % 2 == 0:
                                # 截取到最后一个引号
                                fixed_json = json_str[:i + 1]
                                # 检查是否需要添加闭合括号
                                open_braces = fixed_json.count('{')
                                close_braces = fixed_json.count('}')
                                if open_braces > close_braces:
                                    fixed_json += '\n}'
                                # 尝试解析修复后的JSON
                                result = json.loads(fixed_json)
                                logger.info("成功修复被截断的JSON")
                                break
                    
                    if fixed_json is None:
                        raise ValueError("无法找到有效的结束引号")
                        
                except Exception as fix_error:
                    logger.error(f"JSON修复失败: {str(fix_error)}")
                    logger.error(f"JSON解析失败: {str(e)}, 提取的JSON字符串: {json_str[:1000]}")
                    logger.error(f"原始响应: {ai_response[:1500]}")
                    raise HTTPException(
                        status_code=500,
                        detail='脚本提取失败，AI响应被截断或格式错误，请重试或缩短脚本内容'
                    )
            else:
                logger.error(f"JSON解析失败: {str(e)}, 提取的JSON字符串: {json_str[:500]}")
                logger.error(f"原始响应: {ai_response[:1000]}")
                raise HTTPException(
                    status_code=500,
                    detail='脚本提取失败，AI响应格式错误，请重试'
                )
        
        # 7. 验证是否有脚本
        if not result.get('has_script', False):
            reason = result.get('reason', '对话中未找到完整的脚本内容')
            raise HTTPException(
                status_code=400,
                detail=f'当前对话中未找到完整的脚本内容。{reason}。请先让AI帮您创作脚本'
            )
        
        # 8. 提取脚本数据
        title = result.get('title', '').strip()
        subtitle = result.get('subtitle', '').strip()
        content = result.get('content', '').strip()
        
        if not content:
            raise HTTPException(
                status_code=400,
                detail='提取到的脚本内容为空，请确保对话中包含完整的脚本文案'
            )
        
        # 9. 计算字数
        word_count = len(content)
        
        # 10. 返回结果
        return dict(
            success=True,
            data={
                'title': title,
                'subtitle': subtitle,
                'content': content,
                'word_count': word_count
            }
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"脚本提取失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f'脚本提取失败: {str(e)}'
        )


# ==================== 用户风格档案相关接口 ====================

@app.get('/web/user/style-profile')
@user_required
async def get_user_style_profile(
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取用户风格档案"""
    profile = db.query(UserStyleProfile).filter(
        UserStyleProfile.user_id == current_user.id
    ).first()

    if not profile:
        # 如果不存在,自动创建
        with sm.transaction_scope() as sa:
            profile = UserStyleProfile.create(
                sa,
                user_id=current_user.id,
                is_analyzed=False
            )
            profile.style_dna = {}
            profile.reference_script_ids = []
            profile.analyzed_script_count = 0
            
            # ✅ 在 session 关闭前调用 dump()
            result = profile.dump()
        
        return dict(success=True, data=result)

    return dict(success=True, data=profile.dump())


# ==================== AI对话相关接口 ====================

from .tasks import persist_assistant_reply, schedule_complete_chat_reply
from ..ai.openai_api import _resolve_api_user


def _trim_chat_history(messages: list, max_messages: int, max_chars_per_msg: int) -> list:
    """截取最近 N 条并限制单条长度，避免语音长稿撑爆上下文导致超时/断连。"""
    trimmed = []
    for msg in messages[-max_messages:]:
        text = (msg.content or '').strip()
        if not text:
            continue
        if len(text) > max_chars_per_msg:
            text = text[:max_chars_per_msg] + '\n\n…（前文已截断，仅保留最近内容供 AI 参考）'
        trimmed.append({'role': msg.role, 'content': text})
    return trimmed


def _normalize_script_ids(script_ids):
    if not script_ids:
        return []
    seen = set()
    result = []
    for sid in script_ids:
        try:
            sid = int(sid)
        except (TypeError, ValueError):
            continue
        if sid <= 0 or sid in seen:
            continue
        seen.add(sid)
        result.append(sid)
        if len(result) >= config.CHAT_MAX_REFERENCED_SCRIPTS:
            break
    return result


def _load_user_scripts(db: Session, user_id: int, script_ids: list):
    if not script_ids:
        return []
    scripts = db.query(Script).filter(
        Script.id.in_(script_ids),
        Script.user_id == user_id,
    ).all()
    if len(scripts) != len(script_ids):
        raise HTTPException(status_code=400, detail='部分脚本不存在或无权访问')
    by_id = {script.id: script for script in scripts}
    return [by_id[sid] for sid in script_ids if sid in by_id]


def _build_script_snapshots(scripts: list) -> list:
    snapshots = []
    total_chars = 0
    max_per = config.CHAT_MAX_SCRIPT_REF_CHARS
    max_total = config.CHAT_MAX_SCRIPT_REF_TOTAL_CHARS

    for script in scripts:
        raw_content = (script.content or '').strip()
        word_count = script.word_count
        if word_count is None:
            word_count = len(raw_content)

        truncated = False
        remaining = max_total - total_chars
        limit = min(max_per, remaining) if remaining > 0 else 0
        content = raw_content
        if limit <= 0:
            content = ''
            truncated = True
        elif len(content) > limit:
            content = content[:limit] + '\n\n…（脚本已截断，完整版见脚本库）'
            truncated = True
        total_chars += len(content)

        snapshots.append({
            'id': script.id,
            'title': script.title or '未命名脚本',
            'subtitle': script.subtitle or '',
            'format_type': script.format_type or '',
            'word_count': word_count,
            'content': content,
            'truncated': truncated,
        })
    return snapshots


def _ai_content_for_message(msg: Message, snapshot_override=None) -> str:
    text = (msg.content or '').strip()
    snap = snapshot_override
    if snap is None:
        snap = msg.referenced_scripts_snapshot
    if snap:
        ref_block = build_script_reference_block(snap)
        if ref_block:
            return ref_block + '\n\n---\n\n' + text
    return text


def _trim_chat_messages_dict(messages: list, max_messages: int, max_chars_per_msg: int) -> list:
    trimmed = []
    for item in messages[-max_messages:]:
        text = (item.get('content') or '').strip()
        if not text:
            continue
        if len(text) > max_chars_per_msg:
            text = text[:max_chars_per_msg] + '\n\n…（前文已截断，仅保留最近内容供 AI 参考）'
        trimmed.append({'role': item['role'], 'content': text})
    return trimmed


def _user_profile_for_prompt(user: User) -> dict:
    """从用户资料提取注入 system 的画像（自我介绍 / AI 总结 / 标签）。"""
    introduction = (user.introduction or '').strip() if user.introduction else ''
    ai_summary = (user.ai_summary or '').strip() if user.ai_summary else ''
    tags = user.tags if user.tags else []
    if not isinstance(tags, list):
        tags = []
    if not introduction and not ai_summary and not tags:
        return None
    return {
        'introduction': introduction,
        'ai_summary': ai_summary,
        'tags': tags,
    }


def _build_chat_messages(
    conversation: Conversation,
    db_messages: list,
    user_content: str,
    current_snapshots=None,
    user_profile: dict = None,
) -> list:
    """构建发给模型的消息列表（引用脚本注入到对应 user 消息）。"""
    chat_messages = []
    system_prompt = get_conversation_system_prompt(
        conversation.topic,
        user_profile=user_profile,
    )
    system_prompt = f'{system_prompt}\n{SCRIPT_REFERENCE_USAGE_HINT}'
    chat_messages.append({'role': 'system', 'content': system_prompt})

    history_items = []
    for msg in db_messages:
        if msg.role not in ('user', 'assistant'):
            continue
        content = _ai_content_for_message(msg)
        if content:
            history_items.append({'role': msg.role, 'content': content})

    history_items = _trim_chat_messages_dict(
        history_items,
        config.CHAT_MAX_HISTORY_MESSAGES,
        config.CHAT_MAX_MESSAGE_CHARS,
    )
    for item in history_items:
        chat_messages.append(item)

    if user_content and user_content.strip():
        current_text = user_content.strip()
        if current_snapshots:
            ref_block = build_script_reference_block(current_snapshots)
            if ref_block:
                current_text = ref_block + '\n\n---\n\n' + current_text
        last = chat_messages[-1] if chat_messages else None
        if not last or last.get('role') != 'user' or last.get('content') != current_text:
            chat_messages.append({'role': 'user', 'content': current_text})

    return chat_messages


def _apply_message_script_references(message: Message, script_ids: list, snapshots: list):
    message.referenced_script_ids = script_ids or []
    message.referenced_scripts_snapshot = snapshots or []


@app.post('/web/conversations/chat-stream')
@user_required
async def chat_stream(
    form: ChatStreamForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """AI流式对话接口（SSE）"""
    # 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == form.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    script_ids = _normalize_script_ids(form.referenced_script_ids)
    referenced_scripts = _load_user_scripts(db, current_user.id, script_ids) if script_ids else []
    current_snapshots = _build_script_snapshots(referenced_scripts) if referenced_scripts else []

    if form.message_id:
        with sm.transaction_scope() as sa:
            existing = sa.query(Message).filter(
                Message.id == form.message_id,
                Message.conversation_id == form.conversation_id,
            ).first()
            if not existing:
                raise HTTPException(status_code=404, detail='消息不存在')
            msg = Message.get_or_404(sa, form.message_id)
            if msg.content != form.content:
                msg.content = form.content
            msg.updated_at = datetime.utcnow()
            if form.referenced_script_ids is not None:
                _apply_message_script_references(msg, script_ids, current_snapshots)

    # 获取会话历史消息
    messages = db.query(Message).filter(
        Message.conversation_id == form.conversation_id
    ).order_by(Message.created_at).all()

    # 语音确认等场景：用户消息已在库中，勿重复追加
    pending_user_content = '' if form.message_id else form.content
    pending_snapshots = None if form.message_id else (current_snapshots or None)
    user_profile = _user_profile_for_prompt(current_user)
    chat_messages = _build_chat_messages(
        conversation,
        messages,
        pending_user_content,
        current_snapshots=pending_snapshots,
        user_profile=user_profile,
    )

    if len(messages) > config.CHAT_MAX_HISTORY_MESSAGES:
        logger.info(
            'chat-stream 上下文截断: conversation_id=%s total=%s',
            form.conversation_id,
            len(messages),
        )
    if current_snapshots:
        ref_chars = sum(len((s.get('content') or '')) for s in current_snapshots)
        logger.info(
            'chat-stream 脚本引用: conversation_id=%s script_ids=%s ref_chars=%s',
            form.conversation_id,
            script_ids,
            ref_chars,
        )

    # 创作对话模型（config.CHAT_CONVERSATION_MODEL_TYPE，可选允许 form.model_type 覆盖）
    chat_model_type = resolve_conversation_model_type(form.model_type)
    ai_model = get_chat_ai_model(chat_model_type)
    logger.info(
        "chat-stream: conversation_id=%s request_model_type=%r resolved=%s model=%s",
        form.conversation_id,
        form.model_type,
        chat_model_type,
        ai_model.model_name,
    )

    count_delta = 1 if form.message_id else 2
    api_user_mobile = _resolve_api_user(current_user)

    # 定义流式生成器（客户端断开后仍后台读完并落库）
    async def generate_stream():
        ai_model.reply = ''
        chunk_queue = asyncio.Queue()
        count_delta_local = count_delta

        # 如果传入了message_id，使用已存在的消息，不创建新的用户消息
        if not form.message_id:
            with sm.transaction_scope() as sa:
                user_message = Message.create(
                    sa,
                    conversation_id=form.conversation_id,
                    role='user',
                    content=form.content
                )
                if form.audio_url:
                    user_message.audio_url = form.audio_url
                if form.audio_duration:
                    user_message.audio_duration = form.audio_duration
                if script_ids:
                    _apply_message_script_references(
                        user_message,
                        script_ids,
                        current_snapshots,
                    )

        async def keepalive():
            """首字较慢时定期发 SSE 注释，避免代理/客户端因空闲断连。"""
            try:
                while True:
                    await asyncio.sleep(12)
                    await chunk_queue.put(': keepalive\n\n')
            except asyncio.CancelledError:
                pass

        async def consume_ai():
            try:
                async for chunk in ai_model.reply_stream_text(
                    chat_messages,
                    user_mobile=api_user_mobile,
                ):
                    await chunk_queue.put(chunk)
            except Exception:
                logger.exception(
                    'chat-stream AI 消费异常: conversation_id=%s model_type=%s',
                    form.conversation_id,
                    chat_model_type,
                )
            finally:
                await chunk_queue.put(None)
                ai_text = (getattr(ai_model, 'reply', None) or '').strip()
                if ai_text:
                    persist_assistant_reply(
                        form.conversation_id,
                        ai_text,
                        count_delta_local,
                    )

        consumer_task = asyncio.create_task(consume_ai())
        keepalive_task = asyncio.create_task(keepalive())
        client_disconnected = False

        try:
            while True:
                chunk = await chunk_queue.get()
                if chunk is None:
                    break
                yield chunk
        except asyncio.CancelledError:
            client_disconnected = True
            partial = (getattr(ai_model, 'reply', None) or '').strip()
            logger.warning(
                'chat-stream 客户端断开: conversation_id=%s partial_len=%s',
                form.conversation_id,
                len(partial),
            )
            if partial:
                persist_assistant_reply(
                    form.conversation_id,
                    partial,
                    count_delta_local,
                )
            else:
                schedule_complete_chat_reply(
                    form.conversation_id,
                    chat_messages,
                    count_delta_local,
                    current_user.id,
                    api_user_mobile,
                    chat_model_type,
                )
            raise
        finally:
            keepalive_task.cancel()
            if not client_disconnected:
                try:
                    await consumer_task
                except Exception:
                    logger.exception(
                        'chat-stream 等待 AI 任务失败: conversation_id=%s model_type=%s',
                        form.conversation_id,
                        chat_model_type,
                    )
            elif not consumer_task.done():
                consumer_task.cancel()

    return StreamingResponse(
        generate_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-AI-Provider': chat_model_type,
            'X-AI-Model': ai_model.model_name,
        }
    )


@app.post('/web/conversations/generate-script')
@user_required
async def generate_script(
    form: ScriptGenerateForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """AI生成脚本接口（SSE）"""
    # 验证会话是否属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == form.conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail='会话不存在')

    # 获取会话历史消息
    messages = db.query(Message).filter(
        Message.conversation_id == form.conversation_id
    ).order_by(Message.created_at).all()

    # 获取用户风格档案（如果启用）
    style_context = None
    if form.use_style_profile:
        profile = db.query(UserStyleProfile).filter(
            UserStyleProfile.user_id == current_user.id
        ).first()
        if profile and profile.is_analyzed:
            style_dna = profile.style_dna or {}
            style_context = style_dna.get('summary', '')

    # 构建对话上下文
    conversation_context = []
    for msg in messages[-10:]:  # 最近10条消息
        conversation_context.append({
            "role": msg.role,
            "content": msg.content
        })

    # 使用专业提示词生成脚本提示
    script_prompt = get_script_generation_prompt(
        topic=form.topic,
        format_type=form.format_type,
        requirements=form.requirements,
        style_context=style_context,
        conversation_context=conversation_context
    )

    # 构建消息列表
    chat_messages = []
    
    # 添加历史消息作为上下文
    for msg in messages[-10:]:  # 只取最近10条
        chat_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 添加脚本生成请求
    chat_messages.append({
        "role": "user",
        "content": script_prompt
    })

    chat_model_type = resolve_conversation_model_type(form.model_type)
    ai_model = get_chat_ai_model(chat_model_type)

    # 定义流式生成器
    async def generate_stream():
        script_content = ""
        
        # 调用AI生成脚本
        async for chunk in ai_model.reply_stream_text(chat_messages, current_user):
            yield chunk
            if hasattr(ai_model, 'reply'):
                script_content = ai_model.reply

        # 生成完成后保存脚本
        if script_content:
            with sm.transaction_scope() as sa:
                # 生成脚本标题
                script_title = f"{form.topic} - {form.format_type}脚本"
                
                script = Script.create(
                    sa,
                    user_id=current_user.id,
                    conversation_id=form.conversation_id,
                    title=script_title,
                    content=script_content,
                    format_type=form.format_type,
                    status=ScriptStatus.DRAFT
                )
                script.word_count = len(script_content)
                
                # 更新会话状态
                conv = Conversation.get_or_404(sa, form.conversation_id)
                conv.status = ConversationStatus.COMPLETED
                conv.updated_at = datetime.utcnow()

    return StreamingResponse(
        generate_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


# ==================== 脚本研究相关接口 ====================

@app.get('/web/researches')
@user_required
async def get_researches(
    form: ScriptResearchFilterForm = Depends(),
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取脚本研究列表"""
    query = db.query(ScriptResearch).filter(
        ScriptResearch.user_id == current_user.id
    )
    
    # 关键词过滤（搜索关联的脚本标题）
    if form.keyword:
        query = query.join(Script).filter(
            Script.title.ilike(f'%{form.keyword}%')
        )
    
    # 状态过滤
    if form.status:
        query = query.filter(ScriptResearch.status == form.status)
    
    # 脚本ID过滤
    if form.script_id:
        query = query.filter(ScriptResearch.script_id == form.script_id)
    
    # ✅ 使用子查询：每个脚本只返回最新的一条研究记录
    # 创建子查询，获取每个脚本的最新研究ID
    from sqlalchemy import func
    subquery = db.query(
        ScriptResearch.script_id,
        func.max(ScriptResearch.id).label('max_id')
    ).filter(
        ScriptResearch.user_id == current_user.id
    ).group_by(ScriptResearch.script_id).subquery()
    
    # 只查询每个脚本的最新研究
    query = query.join(
        subquery,
        (ScriptResearch.script_id == subquery.c.script_id) & 
        (ScriptResearch.id == subquery.c.max_id)
    )
    
    # 排序
    query = query.order_by(desc(ScriptResearch.created_at))
    
    # 自定义dump函数，包含脚本信息
    def dump_with_script(r):
        result = r.dump()
        # 获取关联的脚本
        if r.script_id:
            script = db.query(Script).filter(Script.id == r.script_id).first()
            result['script'] = script.dump() if script else None
        else:
            result['script'] = None
        return result
    
    # 使用分页方法
    return ScriptResearch.paginated_dump(
        query=query,
        form=form,
        dump_func=dump_with_script
    )


@app.post('/web/researches')
@user_required
async def start_research(
    form: StartResearchForm,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """开始脚本研究
    
    创建研究会话和研究记录，发送AI的开场白
    如果该脚本已有进行中的研究，则返回现有研究
    """
    # 检查脚本是否存在
    script = db.query(Script).filter(
        Script.id == form.script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')
    
    # ✅ 检查该脚本是否已有进行中的研究
    existing_research = db.query(ScriptResearch).filter(
        ScriptResearch.script_id == form.script_id,
        ScriptResearch.user_id == current_user.id,
        ScriptResearch.status == ResearchStatus.IN_PROGRESS
    ).first()
    
    if existing_research:
        # 如果已有研究，返回现有研究和对话
        conversation = db.query(Conversation).filter(
            Conversation.id == existing_research.conversation_id
        ).first()
        
        # 获取第一条AI消息
        first_ai_message = db.query(Message).filter(
            Message.conversation_id == existing_research.conversation_id,
            Message.role == MessageRole.ASSISTANT.value
        ).order_by(Message.created_at).first()
        
        return dict(
            success=True,
            data={
                'research': existing_research.dump(),
                'conversation': conversation.dump() if conversation else None,
                'initial_message': first_ai_message.dump() if first_ai_message else None,
                'is_existing': True  # 标识这是已存在的研究
            }
        )
    
    with sm.transaction_scope() as sa:
        # 1. 创建研究对话
        conversation = Conversation.create(
            sa,
            user_id=current_user.id,
            title=f"研究脚本：{script.title}",
            topic=script.title,
            conversation_type=ConversationType.RESEARCH,
            status=ConversationStatus.IN_PROGRESS
        )
        conversation.message_count = 0
        conversation.total_tokens = 0
        
        # 2. 创建研究记录
        research = ScriptResearch.create(
            sa,
            user_id=current_user.id,
            script_id=form.script_id,
            conversation_id=conversation.id,
            status=ResearchStatus.IN_PROGRESS
        )
        
        # 3. 设置初始数据
        if form.performance_data:
            research.performance_data = form.performance_data
        
        if form.initial_thoughts:
            research.user_feedback = {
                'initial_thoughts': form.initial_thoughts
            }
        
        # 4. 生成AI开场白
        initial_message_content = get_research_initial_message(
            script_title=script.title,
            performance_data=form.performance_data
        )
        
        # 5. 创建AI开场消息
        ai_message = Message.create(
            sa,
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=initial_message_content
        )
        
        # 6. 更新会话消息数
        conversation.message_count = 1
        
        # ✅ 在 session 关闭前序列化
        research_result = research.dump()
        conversation_result = conversation.dump()
        ai_message_result = ai_message.dump()
    
    return dict(
        success=True,
        data={
            'research': research_result,
            'conversation': conversation_result,
            'initial_message': ai_message_result
        }
    )


@app.get('/web/researches/{research_id}')
@user_required
async def get_research(
    research_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取研究详情"""
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    # 获取关联的脚本
    script = db.query(Script).filter(Script.id == research.script_id).first()
    
    # 获取对话历史
    messages = db.query(Message).filter(
        Message.conversation_id == research.conversation_id
    ).order_by(Message.created_at).all()
    
    return dict(
        success=True,
        data={
            'research': research.dump(),
            'script': script.dump() if script else None,
            'messages': [msg.dump() for msg in messages]
        }
    )


@app.post('/web/researches/{research_id}/chat')
@user_required
async def research_chat(
    research_id: int,
    form: ResearchChatForm,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """研究对话（SSE流式返回）
    
    用户在研究会话中回复AI的问题，AI继续引导和分析
    """
    # 检查研究记录
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    if research.status != ResearchStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail='研究已完成或归档，无法继续对话')
    
    # 获取脚本内容
    script = db.query(Script).filter(Script.id == research.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail='关联的脚本不存在')
    
    # 获取对话历史
    messages = db.query(Message).filter(
        Message.conversation_id == research.conversation_id
    ).order_by(Message.created_at).all()
    
    # 1. 保存用户消息
    with sm.transaction_scope() as sa:
        user_message = Message.create(
            sa,
            conversation_id=research.conversation_id,
            role=MessageRole.USER.value,
            content=form.content
        )
        
        # 更新会话消息数
        conv = Conversation.get_or_404(sa, research.conversation_id)
        conv.message_count = (conv.message_count or 0) + 1
        conv.updated_at = datetime.utcnow()
    
    # 2. 构建系统提示词
    system_prompt = get_research_system_prompt(
        script_content=script.content,
        script_title=script.title,
        performance_data=research.performance_data
    )
    
    # 3. 构建对话上下文（包含系统提示词）
    conversation_history = [
        {
            'role': 'system',
            'content': system_prompt
        }
    ]
    
    # 添加历史消息
    for msg in messages:
        conversation_history.append({
            'role': msg.role,
            'content': msg.content
        })
    
    # 添加当前用户消息
    conversation_history.append({
        'role': MessageRole.USER.value,
        'content': form.content
    })
    
    chat_model_type = resolve_conversation_model_type(form.model_type)
    ai_model = get_chat_ai_model(chat_model_type)

    # 4. 定义流式生成器
    async def generate_stream():
        ai_response_content = ""
        
        try:
            async for chunk in ai_model.reply_stream_text(conversation_history, current_user):
                yield chunk
                if hasattr(ai_model, 'reply'):
                    ai_response_content = ai_model.reply
            
            # 保存AI回复消息
            if ai_response_content:
                with sm.transaction_scope() as sa:
                    ai_message = Message.create(
                        sa,
                        conversation_id=research.conversation_id,
                        role=MessageRole.ASSISTANT.value,
                        content=ai_response_content
                    )
                    
                    # 更新会话统计
                    conv = Conversation.get_or_404(sa, research.conversation_id)
                    conv.message_count = (conv.message_count or 0) + 1
                    conv.updated_at = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"研究对话AI调用失败: {str(e)}")
            error_data = json.dumps({'type': 'error', 'content': f'AI调用失败: {str(e)}'})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


@app.patch('/web/researches/{research_id}')
@user_required
async def update_research_data(
    research_id: int,
    form: UpdateResearchDataForm,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """更新研究数据
    
    灵活更新研究记录的各个字段
    """
    # 检查研究记录
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    with sm.transaction_scope() as sa:
        research_obj = ScriptResearch.get_or_404(sa, research_id)
        
        # 更新各个字段（如果提供）
        if form.performance_data is not None:
            research_obj.performance_data = form.performance_data
        
        if form.key_findings is not None:
            research_obj.key_findings = form.key_findings
        
        if form.user_feedback is not None:
            research_obj.user_feedback = form.user_feedback
        
        if form.ai_analysis is not None:
            research_obj.ai_analysis = form.ai_analysis
        
        if form.success_patterns is not None:
            research_obj.success_patterns = form.success_patterns
        
        if form.summary is not None:
            research_obj.summary = form.summary
        
        research_obj.updated_at = datetime.utcnow()
        
        result = research_obj.dump()
    
    return dict(success=True, data=result)


@app.post('/web/researches/{research_id}/analyze')
@user_required
async def analyze_research(
    research_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """AI分析研究内容
    
    基于对话历史和脚本内容，AI自动分析并生成关键成功要素和总结
    """
    # 检查研究记录
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    if research.status != ResearchStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail='研究已完成或归档')
    
    # 获取对话历史
    conversation = db.query(Conversation).filter(
        Conversation.id == research.conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail='对话记录不存在')
    
    # 获取对话消息
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.role.in_(['user', 'assistant'])
    ).order_by(Message.created_at).all()
    
    if len(messages) < 2:
        raise HTTPException(status_code=400, detail='对话内容不足，无法进行分析')
    
    # 获取脚本内容
    script = db.query(Script).filter(
        Script.id == research.script_id
    ).first()
    
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')
    
    # 构建对话历史文本
    dialogue_text = ""
    for msg in messages:
        role_name = "用户" if msg.role == 'user' else "AI助手"
        dialogue_text += f"{role_name}: {msg.content}\n\n"
    
    # 构建AI分析提示词
    from .prompts import get_research_analyze_prompt
    import json
    import re
    
    analyze_prompt = get_research_analyze_prompt(
        script_title=script.title or "",
        script_content=script.content,
        dialogue_text=dialogue_text
    )
    
    # 直接调用AI进行分析
    try:
        result_text = await reply_text_default(
            messages=[{"role": "user", "content": analyze_prompt}],
            max_tokens=2000,
        )
        
        # 解析AI返回的结果
        try:
            # 尝试提取JSON格式
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # 直接解析
                result = json.loads(result_text)
            
            key_findings = result.get('key_findings', [])
            summary = result.get('summary', '')
            
            # 验证结果
            if not key_findings or len(key_findings) < 1:
                raise ValueError("未能提取到关键成功要素")
            
            if not summary or len(summary) < 10:
                raise ValueError("未能生成有效的研究总结")
            
            # 限制关键要素数量在3-5个
            if len(key_findings) > 5:
                key_findings = key_findings[:5]
            elif len(key_findings) < 3:
                # 如果少于3个，补充提示
                while len(key_findings) < 3:
                    key_findings.append(f"关键要素 {len(key_findings) + 1}（待补充）")
            
            return dict(
                success=True,
                data={
                    'key_findings': key_findings,
                    'summary': summary
                }
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析AI分析结果失败: {str(e)}")
            # 返回默认结果
            return dict(
                success=True,
                data={
                    'key_findings': [
                        "内容结构：脚本整体结构清晰，有明确的开头、主体和结尾",
                        "表达方式：语言简洁有力，符合目标受众的理解水平",
                        "情感共鸣：通过具体案例或场景引发观众共鸣"
                    ],
                    'summary': "这是一个值得深入研究的成功案例。通过分析对话内容和脚本，可以发现其成功的关键在于内容的结构性、表达的准确性以及情感的共鸣。建议在后续创作中继续保持这些优点。"
                }
            )
        
    except Exception as e:
        logger.error(f"AI分析研究内容失败: {str(e)}", exc_info=True)
        # 返回默认结果
        return dict(
            success=True,
            data={
                'key_findings': [
                    "内容结构：脚本整体结构清晰",
                    "表达方式：语言简洁有力",
                    "情感共鸣：能够引发观众共鸣"
                ],
                'summary': "这是一个成功的案例，值得在后续创作中借鉴其经验。"
            }
        )


@app.post('/web/researches/{research_id}/complete')
@user_required
async def complete_research(
    research_id: int,
    form: CompleteResearchForm,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """完成研究
    
    用户确认研究完成，最终确定提炼的经验要素
    """
    # 检查研究记录
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    if research.status != ResearchStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail='研究已完成或归档')
    
    with sm.transaction_scope() as sa:
        research_obj = ScriptResearch.get_or_404(sa, research_id)
        
        # 更新研究结果
        research_obj.key_findings = form.key_findings
        research_obj.summary = form.summary
        research_obj.status = ResearchStatus.COMPLETED
        research_obj.updated_at = datetime.utcnow()
        
        # 更新关联的会话状态
        conv = Conversation.get_or_404(sa, research.conversation_id)
        conv.status = ConversationStatus.COMPLETED
        conv.updated_at = datetime.utcnow()
        
        # 如果需要应用到创作档案
        if form.apply_to_profile:
            # 获取或创建用户风格档案
            style_profile = sa.query(UserStyleProfile).filter(
                UserStyleProfile.user_id == current_user.id
            ).first()
            
            if not style_profile:
                style_profile = UserStyleProfile.create(
                    sa,
                    user_id=current_user.id,
                    is_analyzed=True
                )
                style_profile.reference_script_ids = []
                style_profile.analyzed_script_count = 0
            
            # 更新风格档案
            reference_ids = style_profile.reference_script_ids or []
            if research.script_id not in reference_ids:
                reference_ids.append(research.script_id)
                style_profile.reference_script_ids = reference_ids
            
            style_profile.analyzed_script_count = (style_profile.analyzed_script_count or 0) + 1
            style_profile.last_analysis_at = datetime.utcnow().isoformat()
            style_profile.is_analyzed = True
            style_profile.updated_at = datetime.utcnow()
            
            # TODO: 在后续的任务中，可以异步更新 style_dna
            # 这里先简单地记录研究ID
        
        result = research_obj.dump()
    
    return dict(
        success=True,
        data=result,
        message='研究完成！成功经验已记录'
    )


@app.post('/web/researches/{research_id}/archive')
@user_required
async def archive_research(
    research_id: int,
    form: ArchiveResearchForm,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """归档研究"""
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    with sm.transaction_scope() as sa:
        research_obj = ScriptResearch.get_or_404(sa, research_id)
        research_obj.status = ResearchStatus.ARCHIVED
        research_obj.updated_at = datetime.utcnow()
        
        # 如果提供了归档原因，记录到user_feedback
        if form.archive_reason:
            user_feedback = research_obj.user_feedback or {}
            user_feedback['archive_reason'] = form.archive_reason
            research_obj.user_feedback = user_feedback
        
        result = research_obj.dump()
    
    return dict(success=True, data=result)


@app.delete('/web/researches/{research_id}')
@user_required
async def delete_research(
    research_id: int,
    current_user: User = Depends(get_user),
    db: Session = Depends(sm.get_db)
):
    """删除研究记录"""
    research = db.query(ScriptResearch).filter(
        ScriptResearch.id == research_id,
        ScriptResearch.user_id == current_user.id
    ).first()
    
    if not research:
        raise HTTPException(status_code=404, detail='研究记录不存在')
    
    with sm.transaction_scope() as sa:
        # 删除研究记录
        sa.delete(research)
        
        # 注意：这里不删除关联的Conversation和Message
        # 因为对话记录可能有价值，可以单独保留
    
    return dict(success=True, message='研究记录已删除')


# ─────────────────────────────────────────
#  脚本 AI 生图端点
# ─────────────────────────────────────────

@app.post('/web/scripts/{script_id}/media')
@user_required
async def create_script_media(
    script_id: int,
    form: ScriptMediaForm,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """触发AI为脚本生成素材/封面图（异步任务）"""
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    with sm.transaction_scope() as sa:
        sm_obj = ScriptMedia.create(
            sa,
            user_id=current_user.id,
            script_id=script_id,
            media_type=form.media_type,
            status=ScriptMediaStatus.PENDING.value,
        )
        if form.custom_prompt:
            sm_obj.custom_prompt = form.custom_prompt
        result = sm_obj.dump()

    # 入队 Huey 异步任务
    from .tasks import generate_script_media_task
    generate_script_media_task(result['id'])

    return dict(success=True, data=result)


@app.get('/web/scripts/{script_id}/media')
@user_required
async def list_script_media(
    script_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user)
):
    """获取脚本的所有AI生成素材列表"""
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    script_medias = db.query(ScriptMedia).filter(
        ScriptMedia.script_id == script_id,
        ScriptMedia.user_id == current_user.id
    ).order_by(desc(ScriptMedia.created_at)).all()

    # 批量加载关联的 media 信息
    media_ids = [item.media_id for item in script_medias if item.media_id]
    for item in script_medias:
        for seg in (item.generated_items or []):
            if isinstance(seg, dict) and seg.get('media_id'):
                media_ids.append(seg['media_id'])
    media_map = {}
    if media_ids:
        medias = db.query(MediaModel).filter(MediaModel.id.in_(list(set(media_ids)))).all()
        media_map = {m.id: m for m in medias}

    rows = []
    for item in script_medias:
        data = item.dump()
        if item.media_id and item.media_id in media_map:
            media_obj = media_map[item.media_id]
            data['media_url'] = media_obj.url
            data['media_thumbnail_url'] = media_obj.thumbnail_url

        enriched_items = []
        for seg in (data.get('generated_items') or []):
            if not isinstance(seg, dict):
                continue
            seg_data = dict(seg)
            seg_media_id = seg_data.get('media_id')
            if seg_media_id and seg_media_id in media_map:
                media_obj = media_map[seg_media_id]
                seg_data['media_url'] = media_obj.url
                seg_data['media_thumbnail_url'] = media_obj.thumbnail_url
            enriched_items.append(seg_data)
        data['generated_items'] = enriched_items
        rows.append(data)

    return dict(success=True, data=dict(rows=rows, total=len(rows)))


@app.delete('/web/scripts/{script_id}/media/{media_record_id}')
@user_required
async def delete_script_media(
    script_id: int,
    media_record_id: int,
    current_user: User = Depends(get_user)
):
    """删除脚本AI生成素材记录"""
    with sm.transaction_scope() as sa:
        sm_obj = sa.query(ScriptMedia).filter(
            ScriptMedia.id == media_record_id,
            ScriptMedia.script_id == script_id,
            ScriptMedia.user_id == current_user.id
        ).first()
        if not sm_obj:
            raise HTTPException(status_code=404, detail='素材记录不存在')
        sa.delete(sm_obj)

    return dict(success=True, message='已删除')


@app.get('/web/scripts/{script_id}/share')
@user_required
async def share_script(
    script_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user),
):
    """导出脚本分享包（ZIP：index.html + 本地图片资源）"""
    import io
    from .script_share import build_script_share_zip, build_content_disposition

    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id,
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    zip_bytes, filename = build_script_share_zip(db, script, current_user.id)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type='application/zip',
        headers={
            'Content-Disposition': build_content_disposition(filename),
        },
    )


@app.get('/web/scripts/{script_id}/hyperframes-manifest')
@user_required
async def get_script_hyperframes_manifest(
    script_id: int,
    db: Session = Depends(sm.get_db),
    current_user: User = Depends(get_user),
):
    """导出给 HyperFrames/Codex 使用的脚本与素材清单（只读 JSON，不触发渲染）。"""
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id,
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')

    manifest = _build_hyperframes_manifest(db, script, current_user.id)
    return JSONResponse(content=dict(success=True, data=manifest))


def _build_hyperframes_manifest(db: Session, script: Script, user_id: int):
    from .script_share import collect_script_media_batches

    batches = collect_script_media_batches(db, script.id, user_id)
    media_ids = []
    for batch in batches:
        for item in batch.get('items') or []:
            if item.get('media_id'):
                media_ids.append(item['media_id'])

    media_map = {}
    if media_ids:
        medias = db.query(MediaModel).filter(MediaModel.id.in_(list(set(media_ids)))).all()
        media_map = {m.id: m for m in medias}

    assets = []
    for batch in batches:
        for item in batch.get('items') or []:
            media_id = item.get('media_id')
            media_obj = media_map.get(media_id)
            if not media_obj:
                continue
            assets.append({
                'media_id': media_id,
                'type': batch.get('type_name'),
                'type_label': batch.get('type_label'),
                'label': item.get('label'),
                'segment_index': item.get('segment_index'),
                'url': media_obj.url,
                'thumbnail_url': media_obj.thumbnail_url,
                'filename': media_obj.filename,
            })

    manifest = {
        'version': 1,
        'target': 'hyperframes',
        'script': {
            'id': script.id,
            'title': script.title or '未命名脚本',
            'subtitle': script.subtitle or '',
            'content': script.content or '',
            'format_type': script.format_type or '',
            'word_count': script.word_count or len(script.content or ''),
            'created_at': script.created_at.isoformat() if script.created_at else None,
            'updated_at': script.updated_at.isoformat() if script.updated_at else None,
        },
        'assets': assets,
        'batches': batches,
        'usage_hints': [
            'Use script.content as narration/subtitle source.',
            'Use COVER assets for opening frame or cover animation.',
            'Use MATERIAL assets as B-roll, section cards, or motion backgrounds.',
            'Do not assume every paragraph has an asset; generate simple text/shape scenes when missing.',
        ],
    }
    return manifest


@app.get('/codex/creator/scripts/{script_id}/hyperframes-manifest')
async def codex_get_script_hyperframes_manifest(
    script_id: int,
    user_id: Optional[int] = None,
    x_codex_token: Optional[str] = Header(None, alias='X-Codex-Token'),
    db: Session = Depends(sm.get_db),
):
    """Codex 入口：按 token 导出 HyperFrames manifest。"""
    _verify_codex_token(x_codex_token)
    current_user = _resolve_codex_user(db, user_id)
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id,
    ).first()
    if not script:
        raise HTTPException(status_code=404, detail='脚本不存在')
    manifest = _build_hyperframes_manifest(db, script, current_user.id)
    return JSONResponse(content=dict(success=True, data=manifest))


@app.get('/codex/creator/scripts/hyperframes-manifest')
async def codex_find_script_hyperframes_manifest(
    title: str,
    user_id: Optional[int] = None,
    x_codex_token: Optional[str] = Header(None, alias='X-Codex-Token'),
    db: Session = Depends(sm.get_db),
):
    """Codex 入口：按标题查找最近脚本并导出 HyperFrames manifest。"""
    _verify_codex_token(x_codex_token)
    current_user = _resolve_codex_user(db, user_id)
    title_text = (title or '').strip()
    if not title_text:
        raise HTTPException(status_code=400, detail='title 不能为空')

    script = db.query(Script).filter(
        Script.user_id == current_user.id,
        Script.title == title_text,
    ).order_by(desc(Script.created_at)).first()

    if not script:
        script = db.query(Script).filter(
            Script.user_id == current_user.id,
            Script.title.ilike(f'%{title_text}%'),
        ).order_by(desc(Script.created_at)).first()

    if not script:
        raise HTTPException(status_code=404, detail='未找到匹配标题的脚本')

    manifest = _build_hyperframes_manifest(db, script, current_user.id)
    return JSONResponse(content=dict(success=True, data=manifest))
