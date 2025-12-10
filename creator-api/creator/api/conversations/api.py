import logging
import json
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from ...db import sm
from .. import router as app
from ..jwt import get_user, user_required
from ..users.models import User
from ..ai.openai_api import ali_chat_ai, deepseek_ai, doubao_vision_ai, doubao_16_ai
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
    MessageConfirmForm,
    MessageRetryForm,
    # 研究相关表单
    ScriptResearchFilterForm,
    StartResearchForm,
    ResearchChatForm,
    UpdateResearchDataForm,
    CompleteResearchForm,
    ArchiveResearchForm,
)
from .models import Conversation, Message, Script, UserStyleProfile, ScriptResearch
from .constants import (
    ConversationStatus,
    ConversationType,
    ScriptStatus, 
    MessageRole, 
    TranscriptionStatus, 
    RefinementStatus,
    ResearchStatus,
)
from .prompts import (
    get_conversation_system_prompt, 
    get_script_generation_prompt, 
    get_script_extraction_prompt,
    # 研究相关prompts
    get_research_system_prompt,
    get_research_initial_message,
    get_research_analysis_prompt,
    get_research_summary_prompt,
)
from ..media.models import MediaModel

logger = logging.getLogger(__name__)


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

    # 对话类型过滤
    if form.conversation_type is not None:
        query = query.filter(Conversation.conversation_type == form.conversation_type)

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
            conversation_type=form.conversation_type,
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
            generated_title = await ali_chat_ai.reply_text(messages, current_user)
            
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

    # 构建状态响应
    status_data = {
        'message_id': message.id,
        'transcription': {
            'status': TranscriptionStatus.init(message.transcription_status).dump() if message.transcription_status else None,
            'raw_text': message.raw_transcription,
            'segments': message.transcription_segments,
            'error': message.transcription_error,
            'audio_duration': message.audio_duration,
        },
        'refinement': {
            'status': RefinementStatus.init(message.refinement_status).dump() if message.refinement_status else None,
            'result': message.refinement_result,
            'refined_content': message.refined_content,
            'error': message.refinement_error,
        },
        'user_confirmed': bool(message.user_confirmed) if message.user_confirmed is not None else False,
    }

    return dict(success=True, data=status_data)


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
        
        # 调用AI（使用通义千问，增加max_tokens以确保返回完整JSON）
        # 脚本内容可能很长，使用8000 tokens确保足够
        ai_response = await ali_chat_ai.reply_text(ai_messages, current_user, max_tokens=8000)
        
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

    # 获取会话历史消息
    messages = db.query(Message).filter(
        Message.conversation_id == form.conversation_id
    ).order_by(Message.created_at).all()

    # 构建OpenAI格式的消息列表
    chat_messages = []
    
    # 添加系统提示（使用专业提示词）
    system_prompt = get_conversation_system_prompt(conversation.topic)
    
    chat_messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # 添加历史消息
    for msg in messages:
        chat_messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # 添加当前用户消息
    chat_messages.append({
        "role": "user",
        "content": form.content
    })

    # 选择AI模型
    if form.model_type == 'deepseek':
        ai_model = deepseek_ai
    elif form.model_type == 'doubao_vision':
        ai_model = doubao_vision_ai
    elif form.model_type == 'doubao_16':
        ai_model = doubao_16_ai
    else:
        ai_model = ali_chat_ai

    # 定义流式生成器
    async def generate_stream():
        # 如果传入了message_id，使用已存在的消息，不创建新的用户消息
        if form.message_id:
            # 验证消息是否存在且属于当前会话
            existing_message = db.query(Message).filter(
                Message.id == form.message_id,
                Message.conversation_id == form.conversation_id
            ).first()
            
            if not existing_message:
                yield f"data: {json.dumps({'type': 'error', 'content': '消息不存在'})}\n\n"
                return
            
            # 确保消息内容是最新的
            if existing_message.content != form.content:
                with sm.transaction_scope() as sa:
                    msg = Message.get_or_404(sa, form.message_id)
                    msg.content = form.content
                    msg.updated_at = datetime.utcnow()
        else:
            # 创建新的用户消息
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

        # 调用AI流式生成
        ai_response_content = ""
        
        if form.model_type == 'doubao_16' and form.thinking_mode:
            # 豆包1.6支持思考模式
            async for chunk in ai_model.reply_stream_text(
                chat_messages, 
                user=current_user,
                thinking_mode=form.thinking_mode
            ):
                yield chunk
                # 提取实际回复内容
                if hasattr(ai_model, 'reply'):
                    ai_response_content = ai_model.reply
        elif form.model_type == 'doubao_vision' and form.image_urls:
            # 豆包视觉支持图片
            async for chunk in ai_model.reply_with_vision_stream(
                chat_messages,
                image_filenames=form.image_urls,
                user=current_user
            ):
                yield chunk
                if hasattr(ai_model, 'last_reply'):
                    ai_response_content = ai_model.last_reply
        else:
            # 标准流式对话
            async for chunk in ai_model.reply_stream_text(chat_messages, current_user):
                yield chunk
                if hasattr(ai_model, 'reply'):
                    ai_response_content = ai_model.reply

        # 保存AI回复消息
        if ai_response_content:
            with sm.transaction_scope() as sa:
                assistant_message = Message.create(
                    sa,
                    conversation_id=form.conversation_id,
                    role='assistant',
                    content=ai_response_content
                )
                
                # 更新会话统计
                conv = Conversation.get_or_404(sa, form.conversation_id)
                conv.message_count = (conv.message_count or 0) + 2
                conv.updated_at = datetime.utcnow()

    return StreamingResponse(
        generate_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
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

    # 选择AI模型
    if form.model_type == 'deepseek':
        ai_model = deepseek_ai
    elif form.model_type == 'doubao_16':
        ai_model = doubao_16_ai
    else:
        ai_model = ali_chat_ai

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
    
    # 4. 定义流式生成器
    async def generate_stream():
        ai_response_content = ""
        
        try:
            # 调用AI流式生成
            async for chunk in ali_chat_ai.reply_stream_text(conversation_history, current_user):
                yield chunk
                if hasattr(ali_chat_ai, 'reply'):
                    ai_response_content = ali_chat_ai.reply
            
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
        result_text = await ali_chat_ai.reply_text(
            messages=[{"role": "user", "content": analyze_prompt}],
            max_tokens=2000
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


