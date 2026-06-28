"""
对话相关后台任务
"""
import base64
import logging
import asyncio
import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime

import redis

from ...huey_config import huey
from ...db import sm
from ...config import config
from .models import Message, Conversation, ScriptResearch, Script, UserStyleProfile
from .constants import TranscriptionStatus, RefinementStatus, ResearchStatus, MessageRole
from .prompts import (
    get_refinement_prompt,
    get_research_analysis_prompt,
    get_research_summary_prompt,
    get_style_profile_update_prompt,
)
from .whisper_service import get_whisper_service, extract_audio_segment_to_wav
from ..media.models import MediaModel
from sqlalchemy import desc
from ..ai.openai_api import (
    ali_chat_ai,
    deepseek_ai,
    get_chat_ai_model,
    reply_text_default,
    resolve_conversation_model_type,
    resolve_script_media_plan_model_type,
)
from ..users.models import User

logger = logging.getLogger(__name__)


def persist_assistant_reply(conversation_id: int, content: str, count_delta: int = 1):
    """将 AI 回复写入数据库（幂等：相同正文不重复插入）。"""
    text = (content or '').strip()
    if not text:
        return
    with sm.transaction_scope() as sa:
        last_msg = sa.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).first()

        if (
            last_msg
            and last_msg.role == MessageRole.ASSISTANT.value
            and (last_msg.content or '').strip() == text
        ):
            return

        Message.create(
            sa,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=text
        )
        conv = Conversation.get_or_404(sa, conversation_id)
        conv.message_count = (conv.message_count or 0) + count_delta
        conv.updated_at = datetime.utcnow()
        logger.info(
            '已保存 AI 回复: conversation_id=%s, len=%s',
            conversation_id,
            len(text),
        )


def _run_complete_chat_reply(
    conversation_id: int,
    chat_messages_json: str,
    count_delta: int,
    user_id: int,
    user_mobile: str = None,
    model_type: str = None,
):
    """断线兜底：非流式调用配置的对话模型，写入 assistant 消息。"""
    logger.info(
        '兜底生成 AI 回复: conversation_id=%s user_id=%s model_type=%s',
        conversation_id,
        user_id,
        model_type or config.CHAT_CONVERSATION_MODEL_TYPE,
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        messages = json.loads(chat_messages_json)
        api_user = user_mobile
        if not api_user:
            with sm.transaction_scope() as sa:
                user = User.get_or_404(sa, user_id)
                api_user = user.mobile

        ai_model = get_chat_ai_model(
            model_type or resolve_conversation_model_type()
        )
        text = loop.run_until_complete(
            ai_model.reply_text(messages, user_mobile=api_user)
        )
        if text and str(text).strip():
            persist_assistant_reply(conversation_id, str(text).strip(), count_delta)
        else:
            logger.warning(
                '兜底生成结果为空: conversation_id=%s',
                conversation_id,
            )
    except Exception:
        logger.exception(
            '兜底生成失败: conversation_id=%s',
            conversation_id,
        )
    finally:
        loop.close()


def schedule_complete_chat_reply(
    conversation_id: int,
    chat_messages: list,
    count_delta: int,
    user_id: int,
    user_mobile: str = None,
    model_type: str = None,
):
    """SSE 断开后在独立守护线程中完成 AI 调用（无需 Huey worker）。"""
    payload = json.dumps(chat_messages, ensure_ascii=False)
    thread = threading.Thread(
        target=_run_complete_chat_reply,
        args=(conversation_id, payload, count_delta, user_id, user_mobile, model_type),
        daemon=True,
        name=f'chat-reply-{conversation_id}',
    )
    thread.start()
    logger.info(
        '已启动断线兜底线程: conversation_id=%s thread=%s',
        conversation_id,
        thread.name,
    )


@huey.task()
def complete_chat_reply_task(
    conversation_id: int,
    chat_messages_json: str,
    count_delta: int,
    user_id: int,
):
    """Huey 版断线兜底（可选，与线程版逻辑相同）。"""
    _run_complete_chat_reply(
        conversation_id,
        chat_messages_json,
        count_delta,
        user_id,
    )

# Whisper 在无语音/损坏音频时的常见幻听文本
_WHISPER_PHANTOM_MARKERS = (
    '字幕by', '索兰娅', '谢谢观看', '感谢收看', '请不吝点赞',
    '明镜与点点', 'subtitle', 'amara.org',
)


def _filter_whisper_hallucination(text: str) -> str:
    """仅过滤已知的 Whisper 幻听字幕（不误伤正常短句）"""
    if not text:
        return ''
    normalized = text.strip()
    lower = normalized.lower()
    for marker in _WHISPER_PHANTOM_MARKERS:
        if marker.lower() in lower:
            logger.warning(f'检测到疑似幻听文本，已丢弃: {normalized[:80]}')
            return ''
    return normalized


def _transcribe_chunk_audio(whisper_service, audio_path: str, start_sec: float = 0.0) -> dict:
    """
    转写分块音频：统一转为 16k WAV 再送入 Whisper；空结果时用更大 beam 重试。
    """
    converted_wav_path = None
    try:
        converted_wav_path = extract_audio_segment_to_wav(audio_path, start_sec)
        result = {'text': '', 'duration': 0.0}
        for attempt, beam in enumerate((1, 5), start=1):
            result = whisper_service.transcribe(
                audio_path=converted_wav_path,
                language='zh',
                word_timestamps=False,
                beam_size=beam,
                vad_filter=False,
            )
            raw_text = (result.get('text') or '').strip()
            if raw_text:
                if attempt > 1:
                    logger.info(f'转写重试成功: beam_size={beam}')
                return result
            logger.warning(f'转写结果为空: attempt={attempt}, beam_size={beam}, start_sec={start_sec}')
        return result
    finally:
        if converted_wav_path and os.path.exists(converted_wav_path):
            try:
                os.unlink(converted_wav_path)
            except OSError:
                pass


# ==================== 语音转写任务 ====================

@huey.task()
def transcribe_audio_task(message_id: int):
    """
    语音转写任务
    
    流程：
    1. 获取音频文件
    2. 调用Whisper转写
    3. 保存转写结果
    4. 自动触发整理任务
    """
    logger.info(f"开始转写任务: message_id={message_id}")
    
    try:
        # 1. 获取消息记录
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            audio_media_id = message.audio_media_id
            
            # 更新状态为处理中
            message.transcription_status = TranscriptionStatus.PROCESSING.value
        
        # 2. 获取音频文件路径
        with sm.transaction_scope() as sa:
            media = MediaModel.get_or_404(sa, audio_media_id)
            # 构建完整路径：UPLOADS_DEFAULT_DEST + filename
            audio_path = os.path.join(config.UPLOADS_DEFAULT_DEST, media.filename)
        
        # 3. 调用Whisper转写（带超时检测）
        import time
        
        start_time = time.time()
        timeout_seconds = 300  # 5分钟超时（应该足够处理短音频）
        
        logger.info(f"开始转写，超时时间: {timeout_seconds}秒")
        
        try:
            transcription_result = transcribe_with_whisper(audio_path)
            elapsed_time = time.time() - start_time
            logger.info(f"转写完成，耗时: {elapsed_time:.2f}秒")
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"转写失败，耗时: {elapsed_time:.2f}秒，错误: {str(e)}")
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"转写超时（超过 {timeout_seconds} 秒）")
            raise
        
        # 4. 保存转写结果
        # 先获取需要的数据（在事务外）
        audio_duration = transcription_result.get('duration', 0)
        segments_data = transcription_result.get('segments')
        
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            message.raw_transcription = transcription_result['text']
            message.audio_duration = audio_duration
            message.transcription_status = TranscriptionStatus.COMPLETED.value
            
            # 保存分段信息（transcription_segments 是 @object_property，需要字典格式）
            if segments_data:
                # 如果是列表（短音频情况），转换为字典格式
                if isinstance(segments_data, list):
                    message.transcription_segments = {
                        "segment_count": len(segments_data),
                        "total_duration": audio_duration,
                        "segments": segments_data
                    }
                # 如果是字典（长音频情况），直接使用
                elif isinstance(segments_data, dict):
                    message.transcription_segments = segments_data
        
        # 输出转写结果详情
        logger.info("=" * 80)
        logger.info(f"✅ 转写完成: message_id={message_id}")
        logger.info(f"📝 转写文本长度: {len(transcription_result['text'])} 字符")
        logger.info(f"⏱️  音频时长: {audio_duration:.2f} 秒")
        logger.info(f"📄 转写文本内容:")
        logger.info("-" * 80)
        logger.info(transcription_result['text'])
        logger.info("-" * 80)
        
        # 如果有分段信息，输出分段详情
        if segments_data:
            if isinstance(segments_data, list):
                logger.info(f"📊 分段数量: {len(segments_data)} 段")
                for i, seg in enumerate(segments_data):
                    logger.info(f"   段 {i+1}: [{seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s] {seg.get('text', '')[:50]}...")
            elif isinstance(segments_data, dict):
                segment_count = segments_data.get('segment_count', 0)
                logger.info(f"📊 分段数量: {segment_count} 段")
                segments_list = segments_data.get('segments', [])
                for seg in segments_list:
                    logger.info(f"   段 {seg.get('index', 0)+1}: [{seg.get('start_time', 0):.2f}s - {seg.get('end_time', 0):.2f}s] {seg.get('text', '')[:50]}...")
        
        logger.info("=" * 80)
        
        # 5. 直接标记整理完成（跳过 LLM 校对，由 AI 对话提示词处理口语化文本）
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            message.refinement_status = RefinementStatus.COMPLETED.value
            message.refined_content = transcription_result['text']
            message.refinement_result = {
                'final_text': transcription_result['text'],
                'corrections': []
            }
        
        logger.info(f"✅ 语音处理完成（无 LLM 校对）: message_id={message_id}")
        
    except Exception as e:
        logger.error(f"转写失败: message_id={message_id}, error={str(e)}")
        
        # 保存错误信息
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            message.transcription_status = TranscriptionStatus.FAILED.value
            message.transcription_error = str(e)


def transcribe_with_whisper(audio_path: str) -> dict:
    """
    调用Whisper进行语音转写
    
    参数：
        audio_path: 音频文件路径
    
    返回：
        {
            "text": "完整转写文本",
            "duration": 300,  # 音频时长（秒）
            "segments": {     # 分段信息（仅长音频）
                "segment_count": 3,
                "total_duration": 300,
                "segments": [...]
            }
        }
    """
    logger.info(f"开始Whisper转写: {audio_path}")
    
    try:
        import os
        import sys
        
        # ⚠️ 关键修复：在 Huey 任务中强制使用 CLI 模式（数组输入）
        # 避免输出重定向导致的阻塞问题
        os.environ['DISABLE_OUTPUT_REDIRECT'] = '1'
        
        logger.info(f"🔍 [诊断] 开始获取 WhisperService 实例")
        logger.info(f"🔍 [诊断] 当前进程ID: {os.getpid()}")
        logger.info(f"🔍 [诊断] DISABLE_OUTPUT_REDIRECT={os.environ.get('DISABLE_OUTPUT_REDIRECT')}")
        
        # 获取 WhisperService 实例
        whisper_service = get_whisper_service()
        
        logger.info(f"🔍 [诊断] WhisperService 实例获取成功")
        logger.info(f"🔍 [诊断] 服务类型: {type(whisper_service)}")
        logger.info(f"🔍 [诊断] use_local: {whisper_service.use_local}")
        logger.info(f"🔍 [诊断] model: {whisper_service.model is not None}")
        
        # 强制刷新输出
        sys.stdout.flush()
        sys.stderr.flush()
        
        logger.info(f"🔍 [诊断] 准备调用 transcribe_with_segments()")
        
        # 调用转写服务（带智能分段）
        # 由于设置了 DISABLE_OUTPUT_REDIRECT=1，会使用数组输入模式，避免输出重定向阻塞
        result = whisper_service.transcribe_with_segments(
            audio_path=audio_path,
            max_segment_duration=180,  # 单段最多3分钟
            language="zh"
        )
        
        logger.info(f"🔍 [诊断] transcribe_with_segments() 调用完成")
        logger.info(f"Whisper转写完成: 文本长度={len(result['text'])}, 时长={result['duration']}秒")
        
        return result
        
    except Exception as e:
        logger.error(f"🔍 [诊断] Whisper转写异常捕获")
        logger.error(f"Whisper转写失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise


# ==================== 语音流式分块转写任务 ====================

def _merge_stream_chunks_text(chunks_list: list) -> str:
    sorted_chunks = sorted(chunks_list, key=lambda c: c.get('index', 0))
    return ''.join(c.get('text', '') for c in sorted_chunks).strip()


def _complete_message_transcription(message, chunks_list: list, new_end_time=None, media_id=None) -> bool:
    """将已转写分块合并为最终结果，成功返回 True。"""
    merged_text = _merge_stream_chunks_text(chunks_list)
    if not merged_text:
        return False
    message.raw_transcription = merged_text
    if new_end_time is not None:
        message.audio_duration = int(new_end_time)
    if media_id:
        message.audio_media_id = media_id
    message.transcription_status = TranscriptionStatus.COMPLETED.value
    message.transcription_error = None
    message.refinement_status = RefinementStatus.COMPLETED.value
    message.refined_content = merged_text
    message.refinement_result = {
        'final_text': merged_text,
        'corrections': [],
    }
    return True


def _transcribe_chunk_with_whisper_retry(whisper_service, audio_path: str, prev_end_time: float, max_retries: int = 5):
    """Whisper 冷启动/并发时可能未就绪，短暂重试。"""
    last_error = None
    for attempt in range(max_retries):
        svc = get_whisper_service()
        if svc.use_local and svc.model is None:
            wait = min(2 * (attempt + 1), 10)
            logger.info(f'Whisper 模型未就绪，{wait}s 后重试 ({attempt + 1}/{max_retries})')
            time.sleep(wait)
            continue
        try:
            return _transcribe_chunk_audio(svc, audio_path, prev_end_time)
        except RuntimeError as exc:
            last_error = exc
            if 'Whisper 服务未正确初始化' not in str(exc):
                raise
            wait = min(2 * (attempt + 1), 10)
            logger.warning(f'Whisper 未就绪，{wait}s 后重试 ({attempt + 1}/{max_retries}): {exc}')
            time.sleep(wait)
    if last_error:
        raise last_error
    raise RuntimeError('Whisper 服务未正确初始化：模型未加载且 API 客户端未配置')


_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
        )
    return _redis_client


@contextmanager
def _message_transcribe_lock(message_id: int, timeout_sec: int = 300):
    """同一 message 的转写任务串行执行，避免多 Worker 并发抢 Whisper。"""
    lock = _get_redis_client().lock(
        f'voice_transcribe:{message_id}',
        timeout=timeout_sec,
        blocking_timeout=timeout_sec,
    )
    acquired = lock.acquire(blocking=True)
    if not acquired:
        raise RuntimeError(f'获取语音转写锁超时: message_id={message_id}')
    try:
        yield
    finally:
        try:
            lock.release()
        except Exception:
            pass


def _is_whisper_init_error(exc: Exception) -> bool:
    msg = str(exc)
    return 'Whisper 服务未正确初始化' in msg or 'Whisper 未就绪' in msg


def _schedule_transcribe_retry(message_id, media_id, chunk_index, is_final, delay_sec=5):
    if config.VOICE_TRANSCRIBE_USE_HUEY:
        transcribe_voice_chunk_task.schedule(
            (message_id, media_id, chunk_index, is_final),
            delay=delay_sec,
        )
    else:
        def _retry():
            time.sleep(delay_sec)
            dispatch_transcribe_voice_chunk(
                message_id, media_id, chunk_index, is_final
            )

        threading.Thread(
            target=_retry,
            daemon=True,
            name=f'voice-retry-{message_id}-{chunk_index}',
        ).start()
    logger.info(
        f'已调度转写重试: message_id={message_id}, chunk_index={chunk_index}, '
        f'delay={delay_sec}s'
    )


@huey.task()
def transcribe_voice_chunk_task(message_id: int, media_id: int, chunk_index: int, is_final: bool):
    """
    流式分块语音转写任务
    
    录音过程中定期上传切片并追加到主文件，截取新增音频部分进行 Whisper 转写，
    避免重复处理已转写内容。最终块（is_final=True）合并所有分块文本，
    更新 raw_transcription 并触发整理任务。
    
    流程：
    1. 获取消息的已处理时长（prev_end_time）
    2. 用 ffmpeg 从累积音频中截取 [prev_end_time : ] 的新增部分
    3. Whisper 转写新增部分
    4. 将结果追加到 message.stream_chunks
    5. is_final=True 时：合并所有块文本 → 触发 refine_transcription_task
    """
    logger.info(f"开始分块转写任务: message_id={message_id}, chunk_index={chunk_index}, media_id={media_id}, is_final={is_final}")

    try:
        with _message_transcribe_lock(message_id):
            _run_transcribe_voice_chunk(message_id, media_id, chunk_index, is_final)
    except Exception as e:
        if _is_whisper_init_error(e):
            logger.warning(f'Whisper 未就绪，任务级重试: message_id={message_id}, chunk={chunk_index}')
            _schedule_transcribe_retry(message_id, media_id, chunk_index, is_final, delay_sec=5)
            return
        raise


def _run_transcribe_voice_chunk(message_id: int, media_id: int, chunk_index: int, is_final: bool):
    try:
        # 0. 消息已取消删除则跳过（避免取消录音后仍转写）
        with sm.transaction_scope() as sa:
            message = sa.query(Message).filter(Message.id == message_id).first()
            if not message:
                logger.info(f'消息已删除或不存在，跳过分块转写: message_id={message_id}')
                return

        # 1. 获取音频文件路径 & 上一块的结束时间
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            existing_chunks = message.stream_chunks or {}
            prev_end_time = existing_chunks.get('last_end_time', 0.0)
            chunks_list_existing = existing_chunks.get('chunks', [])

            # 幂等：同一 chunk_index 已处理则跳过
            if any(c.get('index') == chunk_index for c in chunks_list_existing):
                logger.info(f'块 {chunk_index} 已处理，跳过重复任务')
                return

            if chunk_index == 0:
                message.transcription_status = TranscriptionStatus.PROCESSING.value

        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            existing_chunks = message.stream_chunks or {}
            prev_end_time = existing_chunks.get('last_end_time', 0.0)

        with sm.transaction_scope() as sa:
            media = MediaModel.get_or_404(sa, media_id)
            audio_path = os.path.join(config.UPLOADS_DEFAULT_DEST, media.filename)

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        file_size = os.path.getsize(audio_path)
        logger.info(
            f"分块转写: chunk_index={chunk_index}, 截取起点={prev_end_time:.2f}s, "
            f"文件={audio_path}, 大小={file_size} bytes"
        )

        if file_size < 1024:
            raise ValueError(
                f'录音文件过小（{file_size} 字节），可能是麦克风未采集到声音，请检查系统麦克风权限与输入设备'
            )

        os.environ['DISABLE_OUTPUT_REDIRECT'] = '1'

        transcription = _transcribe_chunk_with_whisper_retry(
            None, audio_path, prev_end_time
        )

        chunk_duration = transcription.get('duration', 0.0)
        raw_text = (transcription.get('text') or '').strip()
        chunk_text = _filter_whisper_hallucination(raw_text)
        new_end_time = prev_end_time + chunk_duration

        logger.info(
            f"块 {chunk_index} 转写: 原始={raw_text[:80] if raw_text else '(空)'}, "
            f"过滤后={chunk_text[:80] if chunk_text else '(空)'}, "
            f"片段时长={chunk_duration:.2f}s"
        )

        if is_final and not chunk_text:
            if raw_text:
                # 仅被幻听过滤器去掉时，保留原始文本
                chunk_text = raw_text
                logger.warning(f'幻听过滤后为空，保留原始转写: {raw_text[:80]}')
            elif chunk_duration < 1.0:
                raise ValueError(
                    '录音时长过短或未检测到声音，请靠近麦克风说话后重试'
                )
            else:
                raise ValueError(
                    '未识别到语音内容。请确认浏览器已允许麦克风，并在系统设置中选择了正确的输入设备'
                )

        # 3. 将结果追加到 message.stream_chunks
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)

            current_stream = message.stream_chunks or {'chunks': [], 'last_end_time': 0.0}
            chunks_list = current_stream.get('chunks', [])

            if any(c.get('index') == chunk_index for c in chunks_list):
                logger.info(f'块 {chunk_index} 已写入，跳过重复追加')
                return

            chunks_list.append({
                'index': chunk_index,
                'media_id': media_id,
                'text': chunk_text,
                'end_time': new_end_time
            })

            # 更新 stream_chunks
            message.stream_chunks = {
                'chunks': chunks_list,
                'last_end_time': new_end_time
            }
            message.stream_chunk_count = len(chunks_list)

            # 后续块成功时清除先前非最终块失败留下的 FAILED 状态
            if message.transcription_status == TranscriptionStatus.FAILED.value:
                message.transcription_status = TranscriptionStatus.PROCESSING.value
                message.transcription_error = None

            if is_final:
                # 5. 合并所有块文本，完成转写
                if _complete_message_transcription(
                    message,
                    chunks_list,
                    new_end_time=new_end_time,
                    media_id=media_id,
                ):
                    logger.info(
                        f"分块转写全部完成: message_id={message_id}, "
                        f"共 {len(chunks_list)} 块, 合并文本={len(message.raw_transcription)} 字"
                    )
                else:
                    raise ValueError(
                        '未识别到有效语音内容，请检查麦克风权限与音量后重试'
                    )

    except Exception as e:
        logger.error(f"分块转写失败: message_id={message_id}, chunk_index={chunk_index}, error={str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        with sm.transaction_scope() as sa:
            message = sa.query(Message).filter(Message.id == message_id).first()
            if not message:
                logger.info(f'消息已删除，跳过转写失败状态写入: message_id={message_id}')
                return

            current_stream = message.stream_chunks or {'chunks': [], 'last_end_time': 0.0}
            chunks_list = current_stream.get('chunks', [])

            # Whisper 冷启动/未就绪是可恢复错误，不应写成 FAILED 暴露给前端。
            if _is_whisper_init_error(e):
                message.transcription_status = TranscriptionStatus.PROCESSING.value
                message.transcription_error = None
                _schedule_transcribe_retry(message_id, media_id, chunk_index, is_final)
                return

            # 最终块失败但已有分块：合并已有结果，避免前序块白转
            if is_final and chunks_list:
                if _complete_message_transcription(
                    message,
                    chunks_list,
                    new_end_time=current_stream.get('last_end_time', 0.0),
                ):
                    logger.info(
                        f'最终块失败但已有分块，合并完成: message_id={message_id}, '
                        f'共 {len(chunks_list)} 块'
                    )
                    return

            # 非最终块失败：保留已识别分块，继续等待后续块
            if not is_final:
                if chunks_list:
                    message.transcription_status = TranscriptionStatus.PROCESSING.value
                    message.transcription_error = None
                    logger.warning(
                        f'块 {chunk_index} 转写失败，保留已有 {len(chunks_list)} 块继续处理: {str(e)}'
                    )
                elif chunk_index == 0:
                    message.transcription_status = TranscriptionStatus.FAILED.value
                    message.transcription_error = f"块 {chunk_index} 转写失败: {str(e)}"
                else:
                    # 后续块失败且尚无分块：多为并发抢跑，不回写 FAILED，等待前序块
                    message.transcription_status = TranscriptionStatus.PROCESSING.value
                    message.transcription_error = None
                    logger.warning(
                        f'块 {chunk_index} 转写失败（前序块可能仍在处理），忽略: {str(e)}'
                    )
                return

            message.transcription_status = TranscriptionStatus.FAILED.value
            message.transcription_error = f"块 {chunk_index} 转写失败: {str(e)}"


def dispatch_transcribe_voice_chunk(
    message_id: int,
    media_id: int,
    chunk_index: int,
    is_final: bool,
):
    """分发语音分块转写：默认在 API 进程内执行（复用已预热的 Whisper）。"""
    if config.VOICE_TRANSCRIBE_USE_HUEY:
        return transcribe_voice_chunk_task(
            message_id, media_id, chunk_index, is_final
        )

    def _runner():
        try:
            logger.info(
                '开始 in-process 分块转写: message_id=%s, chunk_index=%s, is_final=%s',
                message_id, chunk_index, is_final,
            )
            with _message_transcribe_lock(message_id):
                _run_transcribe_voice_chunk(
                    message_id, media_id, chunk_index, is_final
                )
        except Exception as exc:
            logger.exception(
                'in-process 分块转写异常: message_id=%s, chunk=%s, error=%s',
                message_id, chunk_index, exc,
            )

    threading.Thread(
        target=_runner,
        daemon=True,
        name='voice-transcribe-%s-%s' % (message_id, chunk_index),
    ).start()
    return 'in-process'


@huey.task()
def finalize_voice_transcription_task(message_id: int):
    """流式录音结束收尾：合并已转写分块（最后 stop 可能无有效尾片）。"""
    _finalize_voice_transcription(message_id)


def _finalize_voice_transcription(message_id: int):
    """收尾逻辑（API 同步调用 / Huey 异步任务共用）。"""
    logger.info(f"收尾语音转写: message_id={message_id}")
    try:
        with sm.transaction_scope() as sa:
            message = sa.query(Message).filter(Message.id == message_id).first()
            if not message:
                logger.info(f'消息已删除，跳过收尾: message_id={message_id}')
                return
            if message.transcription_status == TranscriptionStatus.COMPLETED.value:
                return

            current_stream = message.stream_chunks or {'chunks': [], 'last_end_time': 0.0}
            chunks_list = current_stream.get('chunks', [])
            if not chunks_list:
                message.transcription_status = TranscriptionStatus.FAILED.value
                message.transcription_error = '未采集到有效录音，请检查麦克风权限与输入设备'
                return

            sorted_chunks = sorted(chunks_list, key=lambda c: c['index'])
            merged_text = ''.join(c.get('text', '') for c in sorted_chunks).strip()
            new_end_time = current_stream.get('last_end_time', 0.0)

            message.raw_transcription = merged_text
            message.audio_duration = int(new_end_time)
            message.transcription_status = TranscriptionStatus.COMPLETED.value
            message.transcription_error = None
            message.refinement_status = RefinementStatus.COMPLETED.value
            message.refined_content = merged_text
            message.refinement_result = {
                'final_text': merged_text,
                'corrections': [],
            }

            if not merged_text:
                message.transcription_status = TranscriptionStatus.FAILED.value
                message.transcription_error = (
                    '未识别到有效语音内容，请确认麦克风权限与音量后重试'
                )
                return

            logger.info(
                f"语音转写收尾完成: message_id={message_id}, "
                f"共 {len(chunks_list)} 块, 合并文本={len(merged_text)} 字"
            )
    except Exception as e:
        logger.error(f"收尾语音转写失败: message_id={message_id}, error={str(e)}")
        with sm.transaction_scope() as sa:
            message = sa.query(Message).filter(Message.id == message_id).first()
            if not message:
                return
            message.transcription_status = TranscriptionStatus.FAILED.value
            message.transcription_error = f"收尾转写失败: {str(e)}"


# ==================== 语音识别校对任务 ====================

@huey.task()
def refine_transcription_task(message_id: int):
    """
    语音识别校对任务
    
    流程：
    1. 获取原始转写文本
    2. 调用LLM进行校对和修正
    3. 保存校对结果
    """
    logger.info(f"开始校对任务: message_id={message_id}")
    
    try:
        # 1. 获取消息和转写文本
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            raw_text = message.raw_transcription
            conversation_id = message.conversation_id
            audio_duration = message.audio_duration or 0
            
            # 更新状态为处理中
            message.refinement_status = RefinementStatus.PROCESSING.value
        
        if not raw_text:
            raise ValueError("转写文本为空")
        
        # 2. 获取对话上下文
        conversation_context = get_conversation_context(conversation_id)
        
        # 3. 调用LLM进行校对和修正
        refinement_result = refine_content_with_llm(
            raw_text=raw_text,
            conversation_context=conversation_context,
            audio_duration=audio_duration
        )
        
        # 4. 保存校对结果
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            message.refinement_result = refinement_result
            message.refined_content = refinement_result.get('final_text', '')
            message.refinement_status = RefinementStatus.COMPLETED.value
        
        logger.info(f"校对完成: message_id={message_id}")
        
    except Exception as e:
        logger.error(f"校对失败: message_id={message_id}, error={str(e)}")
        
        # 保存错误信息
        with sm.transaction_scope() as sa:
            message = Message.get_or_404(sa, message_id)
            message.refinement_status = RefinementStatus.FAILED.value
            message.refinement_error = str(e)


def get_conversation_context(conversation_id: int) -> str:
    """
    获取对话上下文（会话主题和最近的几条消息）
    """
    try:
        with sm.transaction_scope() as sa:
            conversation = Conversation.get_or_404(sa, conversation_id)
            
            # 获取会话主题
            context = f"会话主题: {conversation.topic}\n\n"
            
            # 获取最近3条已确认的用户消息
            recent_messages = sa.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.role == 'user',
                Message.user_confirmed == 1
            ).order_by(Message.created_at.desc()).limit(3).all()
            
            if recent_messages:
                context += "最近的对话：\n"
                for msg in reversed(recent_messages):  # 按时间正序
                    context += f"- {msg.content[:100]}...\n"
            
            return context
    except Exception as e:
        logger.warning(f"获取对话上下文失败: {str(e)}")
        return ""


def refine_content_with_llm(raw_text: str, conversation_context: str = "", audio_duration: int = 0) -> dict:
    """
    使用LLM校对和修正语音识别错误
    
    参数：
        raw_text: 原始转写文本
        conversation_context: 对话上下文
        audio_duration: 音频时长（秒）
    
    返回：
        {
            "final_text": "校对后的完整文本",
            "corrections": [
                {
                    "original": "原始错误文本",
                    "corrected": "修正后的文本",
                    "reason": "修正原因"
                }
            ]
        }
    """
    logger.info(f"开始LLM校对: 原文长度={len(raw_text)}, 音频时长={audio_duration}秒")
    
    try:
        # 构建校对提示词
        prompt = get_refinement_prompt(
            raw_text=raw_text,
            conversation_context=conversation_context,
            audio_duration=audio_duration
        )
        
        # 构建消息列表
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 调用LLM API（使用DeepSeek，性价比高）
        # 在后台任务中调用异步函数，需要使用 asyncio.run
        try:
            result_text = asyncio.run(
                deepseek_ai.reply_text(
                    messages=messages,
                    user=None,
                    response_format='json_object'
                )
            )
        except Exception as api_error:
            logger.warning(f"DeepSeek调用失败，尝试通义千问: {str(api_error)}")
            # 如果DeepSeek失败，尝试通义千问
            result_text = asyncio.run(
                ali_chat_ai.reply_text(
                    messages=messages,
                    user=None,
                    response_format='json_object'
                )
            )
        
        if not result_text:
            raise ValueError("LLM返回空结果")
        
        # 解析JSON结果
        result = json.loads(result_text)
        
        # 验证必要字段
        if "final_text" not in result:
            logger.warning("LLM返回结果缺少字段: final_text")
            result["final_text"] = raw_text  # 降级：使用原始文本
        
        # 确保可选字段存在
        result.setdefault("corrections", [])
        
        # 输出校对结果详情
        corrections_count = len(result.get("corrections", []))
        if corrections_count > 0:
            logger.info(f"LLM校对完成: 修正了 {corrections_count} 处错误")
            for i, correction in enumerate(result.get("corrections", [])[:5], 1):  # 最多显示5处
                logger.info(f"  修正 {i}: '{correction.get('original', '')}' → '{correction.get('corrected', '')}' ({correction.get('reason', '')})")
        else:
            logger.info(f"LLM校对完成: 未发现需要修正的错误")
        
        logger.info(f"校对后文本: {result.get('final_text', '')[:100]}...")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM返回结果JSON解析失败: {str(e)}, 原文: {result_text[:500]}")
        # 返回降级结果
        return {
            "corrections": [],
            "final_text": raw_text
        }
    except Exception as e:
        logger.error(f"LLM校对失败: {str(e)}")
        # 返回基础校对结果（降级处理）
        return {
            "corrections": [],
            "final_text": raw_text
        }


# ==================== 脚本研究任务 ====================

@huey.task()
def analyze_research_task(research_id: int):
    """
    AI深度分析任务
    
    在研究对话进行到一定程度后，触发此任务进行深度分析。
    分析维度：内容、结构、语言、受众等。
    
    Args:
        research_id: 研究记录ID
    """
    logger.info(f"开始AI深度分析任务: research_id={research_id}")
    
    try:
        # 1. 获取研究记录和相关数据
        with sm.transaction_scope() as sa:
            research = ScriptResearch.get_or_404(sa, research_id)
            script = Script.get_or_404(sa, research.script_id)
            
            # 获取对话历史
            messages = sa.query(Message).filter(
                Message.conversation_id == research.conversation_id
            ).order_by(Message.created_at).all()
            
            conversation_history = [
                {
                    'role': msg.role,
                    'content': msg.content
                }
                for msg in messages
            ]
            
            # 提取用户反馈摘要
            user_messages = [msg.content for msg in messages if msg.role == 'user']
            user_feedback_summary = '\n'.join(user_messages) if user_messages else None
        
        # 2. 构建分析提示词
        analysis_prompt = get_research_analysis_prompt(
            script_content=script.content,
            script_title=script.title,
            conversation_history=conversation_history,
            user_feedback_summary=user_feedback_summary
        )
        
        # 3. 调用AI进行分析
        logger.info("调用AI进行深度分析...")
        analysis_result = asyncio.run(
            reply_text_default(
                messages=[
                    {'role': 'system', 'content': '你是一个专业的内容分析专家。'},
                    {'role': 'user', 'content': analysis_prompt},
                ],
                response_format='json_object',
            )
        )
        
        # 4. 解析分析结果（JSON格式）
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', analysis_result, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
            else:
                # 尝试直接解析
                analysis_json = json.loads(analysis_result)
            
            logger.info("AI分析完成，成功解析结果")
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"解析AI分析结果失败: {str(e)}")
            # 使用降级的分析结果
            analysis_json = {
                "content_analysis": {
                    "theme": "未能解析",
                    "angle": "未能解析",
                    "information_density": "medium",
                    "value_proposition": "未能解析"
                },
                "structure_analysis": {},
                "language_style": {},
                "audience_positioning": {}
            }
        
        # 5. 保存分析结果
        with sm.transaction_scope() as sa:
            research_obj = ScriptResearch.get_or_404(sa, research_id)
            research_obj.ai_analysis = analysis_json
            research_obj.updated_at = datetime.utcnow()
            
            logger.info(f"AI分析结果已保存: research_id={research_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"AI深度分析任务失败: {str(e)}", exc_info=True)
        
        # 标记分析失败
        try:
            with sm.transaction_scope() as sa:
                research_obj = ScriptResearch.get_or_404(sa, research_id)
                user_feedback = research_obj.user_feedback or {}
                user_feedback['analysis_error'] = str(e)
                research_obj.user_feedback = user_feedback
        except:
            pass
        
        raise


@huey.task()
def generate_research_summary_task(research_id: int):
    """
    生成研究总结任务
    
    基于关键发现和AI分析，生成简洁的研究总结。
    
    Args:
        research_id: 研究记录ID
    """
    logger.info(f"开始生成研究总结: research_id={research_id}")
    
    try:
        # 1. 获取研究数据
        with sm.transaction_scope() as sa:
            research = ScriptResearch.get_or_404(sa, research_id)
            script = Script.get_or_404(sa, research.script_id)
            
            key_findings = research.key_findings or []
            ai_analysis = research.ai_analysis or {}
            user_feedback = research.user_feedback or {}
        
        if not key_findings:
            logger.warning(f"研究记录缺少关键发现，无法生成总结: research_id={research_id}")
            return False
        
        # 2. 构建总结提示词
        summary_prompt = get_research_summary_prompt(
            script_title=script.title,
            key_findings=key_findings,
            ai_analysis=ai_analysis,
            user_feedback=user_feedback
        )
        
        # 3. 调用AI生成总结
        logger.info("调用AI生成研究总结...")
        summary_text = asyncio.run(
            reply_text_default(
                messages=[
                    {'role': 'system', 'content': '你是一个专业的内容总结专家。'},
                    {'role': 'user', 'content': summary_prompt},
                ],
            )
        )
        
        # 4. 保存总结
        with sm.transaction_scope() as sa:
            research_obj = ScriptResearch.get_or_404(sa, research_id)
            research_obj.summary = summary_text.strip()
            research_obj.updated_at = datetime.utcnow()
            
            logger.info(f"研究总结已生成并保存: research_id={research_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"生成研究总结任务失败: {str(e)}", exc_info=True)
        raise


@huey.task()
def update_style_profile_task(user_id: int, research_id: int):
    """
    更新用户创作风格档案任务
    
    基于新的研究结果，更新或丰富用户的创作风格档案。
    
    Args:
        user_id: 用户ID
        research_id: 研究记录ID
    """
    logger.info(f"开始更新用户风格档案: user_id={user_id}, research_id={research_id}")
    
    try:
        # 1. 获取现有风格档案和新研究结果
        with sm.transaction_scope() as sa:
            # 获取或创建风格档案
            style_profile = sa.query(UserStyleProfile).filter(
                UserStyleProfile.user_id == user_id
            ).first()
            
            if not style_profile:
                style_profile = UserStyleProfile.create(
                    sa,
                    user_id=user_id,
                    is_analyzed=False
                )
                style_profile.style_dna = {}
                style_profile.reference_script_ids = []
                style_profile.analyzed_script_count = 0
            
            existing_profile = style_profile.style_dna or {}
            
            # 获取新研究
            research = ScriptResearch.get_or_404(sa, research_id)
            new_research = {
                'key_findings': research.key_findings or [],
                'success_patterns': research.success_patterns or [],
                'ai_analysis': research.ai_analysis or {}
            }
        
        # 2. 构建更新提示词
        update_prompt = get_style_profile_update_prompt(
            user_existing_profile=existing_profile,
            new_research=new_research
        )
        
        # 3. 调用AI生成更新后的档案
        logger.info("调用AI更新风格档案...")
        updated_profile_text = asyncio.run(
            reply_text_default(
                messages=[
                    {'role': 'system', 'content': '你是一个专业的用户画像分析师。'},
                    {'role': 'user', 'content': update_prompt},
                ],
                response_format='json_object',
            )
        )
        
        # 4. 解析更新结果（JSON格式）
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', updated_profile_text, re.DOTALL)
            if json_match:
                updated_profile = json.loads(json_match.group(1))
            else:
                updated_profile = json.loads(updated_profile_text)
            
            logger.info("风格档案更新成功解析")
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"解析风格档案更新结果失败: {str(e)}")
            # 使用简化的更新（只添加新的参考脚本）
            updated_profile = existing_profile
        
        # 5. 保存更新后的档案
        with sm.transaction_scope() as sa:
            style_profile_obj = sa.query(UserStyleProfile).filter(
                UserStyleProfile.user_id == user_id
            ).first()
            
            if style_profile_obj:
                style_profile_obj.style_dna = updated_profile
                style_profile_obj.is_analyzed = True
                style_profile_obj.last_analysis_at = datetime.utcnow().isoformat()
                style_profile_obj.updated_at = datetime.utcnow()
                
                logger.info(f"用户风格档案已更新: user_id={user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新用户风格档案任务失败: {str(e)}", exc_info=True)
        raise


@huey.task()
def extract_success_patterns_task(research_id: int):
    """
    提取成功模式任务
    
    从研究记录中提取可复用的成功模式。
    这个任务会分析用户反馈和AI分析，识别出具体的创作模式。
    
    Args:
        research_id: 研究记录ID
    """
    logger.info(f"开始提取成功模式: research_id={research_id}")
    
    try:
        # 1. 获取研究数据
        with sm.transaction_scope() as sa:
            research = ScriptResearch.get_or_404(sa, research_id)
            
            key_findings = research.key_findings or []
            ai_analysis = research.ai_analysis or {}
            user_feedback = research.user_feedback or {}
        
        if not key_findings or not ai_analysis:
            logger.warning(f"研究记录数据不完整，无法提取成功模式: research_id={research_id}")
            return False
        
        # 2. 构建提取提示词
        patterns_prompt = f"""基于以下研究结果，提取可复用的成功模式。

## 关键发现
{json.dumps(key_findings, ensure_ascii=False, indent=2)}

## AI分析
{json.dumps(ai_analysis, ensure_ascii=False, indent=2)}

## 任务
请识别出3-5个具体的、可复用的创作模式。每个模式包括：
- pattern_type: 模式类型（opening/structure/language/closing等）
- pattern_name: 模式名称（简洁描述）
- description: 详细描述（如何应用）
- confidence: 置信度（0-1，基于证据强度）

## 输出格式
请输出JSON格式：

```json
[
  {{
    "pattern_type": "opening",
    "pattern_name": "痛点场景式开头",
    "description": "用具体的场景+痛点，快速抓住目标观众的注意力",
    "confidence": 0.9
  }},
  ...
]
```

现在请开始提取："""
        
        # 3. 调用AI提取模式
        logger.info("调用AI提取成功模式...")
        patterns_text = asyncio.run(
            reply_text_default(
                messages=[
                    {'role': 'system', 'content': '你是一个专业的内容模式识别专家。'},
                    {'role': 'user', 'content': patterns_prompt},
                ],
                response_format='json_object',
            )
        )
        
        # 4. 解析提取结果
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', patterns_text, re.DOTALL)
            if json_match:
                patterns = json.loads(json_match.group(1))
            else:
                patterns = json.loads(patterns_text)
            
            logger.info(f"成功提取 {len(patterns)} 个成功模式")
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"解析成功模式失败: {str(e)}")
            patterns = []
        
        # 5. 保存成功模式
        if patterns:
            with sm.transaction_scope() as sa:
                research_obj = ScriptResearch.get_or_404(sa, research_id)
                research_obj.success_patterns = patterns
                research_obj.updated_at = datetime.utcnow()
                
                logger.info(f"成功模式已保存: research_id={research_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"提取成功模式任务失败: {str(e)}", exc_info=True)
        raise


# ─────────────────────────────────────────
#  脚本 AI 生图
# ─────────────────────────────────────────

def _parse_ai_json_response(text: str) -> dict:
    """从 AI 回复中解析 JSON 对象。"""
    import re
    raw = (text or '').strip()
    if not raw:
        return {}
    json_match = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1).strip()
    return json.loads(raw)


def _build_cover_image_prompt(plan: dict, orientation: str = 'portrait') -> str:
    """根据封面规划结果组装最终生图提示词（核心词大字 + 一句话小字）。

    orientation: 'portrait' 竖版 3:4 | 'landscape' 横版 4:3
    """
    headline = (plan.get('cover_headline') or '').strip()
    subline = (plan.get('cover_subline') or '').strip()
    base_prompt = (plan.get('image_prompt') or '').strip()
    visual_bits = plan.get('key_visual_elements') or []
    visual_text = '、'.join([str(x).strip() for x in visual_bits if str(x).strip()])

    is_landscape = orientation == 'landscape'
    aspect_label = '横版 4:3' if is_landscape else '竖版 3:4'
    layout_hint = (
        '横版 4:3 短视频封面，4K，人物与信息图左右分布，标题文字块位于画面垂直 35%-45%、水平居中，'
        '不遮挡人物面部与屏幕核心内容。'
        if is_landscape else
        '竖版 3:4 短视频封面，4K，左侧人物半身/背影/侧脸，右侧架构图/白板/屏幕，'
        '标题文字块位于画面垂直 35%-45%、水平居中，不贴顶、不遮挡人物与屏幕。'
    )

    if headline and subline:
        text_block = (
            f'画面文案分两层且语义一体：第一层超大号加粗主标题「{headline}」，'
            f'使用粗黑体/标题黑体/几何无衬线黑体，白色或近白色，'
            f'带轻微冷蓝描边和深色硬投影，边缘清晰、视觉重量强、手机小图可读。'
            f'第二层较小字号副标题「{subline}」紧接主标题下方，'
            f'字号约为主标题的 40%-55%，使用亮青色、电蓝色或高对比白色，'
            f'带足够描边/投影，不要融进背景。'
            f'主副标题作为一组标题块，整体位于画面垂直方向 35%-45%（略偏中心、绝不贴顶），水平居中；'
            f'标题上方和下方都要留出足够空间，复杂视觉元素放在标题区域以外。'
            f'副标题是对主标题的直接补充/解释，读在一起是一条完整封面信息，'
            f'层级清晰、对比强烈、中文清晰可读。'
            f'标题区域必须有干净留白或暗色衬底，文字不能压在复杂细节、人物头发、屏幕内容或强光区域上。'
            f'不要花哨变形字、金属 3D 爆炸字、彩虹渐变字、过度霓虹或过强外发光。'
        )
        if base_prompt and headline in base_prompt and subline in base_prompt and not is_landscape:
            return base_prompt
        style = base_prompt if (base_prompt and not is_landscape) else (
            f'{layout_hint}专业克制、真实技术人风格，色彩鲜明但不过度炫技。'
            f'画面采用真实工作台/屏幕/白板/简洁流程图组合（{visual_text or "五层架构卡片、工作流白板、代码屏幕"}），'
            f'可出现无明确身份的技术人半身、背影或侧脸轮廓，避免纯抽象 AI 光效中心构图。'
            f'不要具体平台 Logo，不要二维码，不要名人脸。'
            f'避免爆炸光效、巨大 3D 光圈、能量箭头、破碎粒子、漂浮图标堆叠、赛博朋克过载。'
        )
        return f'{aspect_label}。{style} {text_block}'

    return base_prompt


def _build_material_image_prompt(prompt: str) -> str:
    """给脚本素材图追加统一风格约束，避免生成复杂产品后台或营销大屏。"""
    base = (prompt or '').strip()
    if not base:
        return ''
    material_guard = (
        ' 统一要求：这是口播视频中的横版 4:3 B-roll 讲解素材，不是产品宣传海报，'
        '画面要像真实技术人的白板推演、工作台草图或简洁信息图。'
        '优先使用便签卡片、白板、流程箭头、简洁架构框、屏幕草图。'
        '禁止生成完整 SaaS 后台、复杂数据大屏、假任务列表、假日期、假负责人、KPI、密集表格。'
        '每张图最多 1 个主标题和 6 个短标签，中文大字清晰可读，不要大段小字。'
        '不要平台 Logo、二维码、网址、真实公司名、真实人名。'
        '深色蓝紫科技风可以保留，但降低光效密度，避免爆炸光效、巨大 3D 核心、漂浮图标堆叠。'
    )
    return f'{base}{material_guard}'


def _plan_script_media_with_ai(
    *,
    media_type_value: int,
    title: str,
    subtitle: str,
    content: str,
    custom_prompt: str = None,
) -> dict:
    """调用 OpenAIGptAI 分析脚本并规划生图方案。"""
    from .constants import ScriptMediaType
    from .script_media_prompts import (
        get_script_media_plan_system_prompt,
        get_script_cover_plan_prompt,
        get_script_material_plan_prompt,
    )

    if media_type_value == ScriptMediaType.COVER.value:
        user_prompt = get_script_cover_plan_prompt(
            title=title,
            subtitle=subtitle,
            content=content,
            custom_prompt=custom_prompt,
        )
    else:
        user_prompt = get_script_material_plan_prompt(
            title=title,
            subtitle=subtitle,
            content=content,
            custom_prompt=custom_prompt,
        )

    plan_model = get_chat_ai_model(resolve_script_media_plan_model_type())
    result_text = asyncio.run(
        plan_model.reply_text(
            messages=[
                {'role': 'system', 'content': get_script_media_plan_system_prompt()},
                {'role': 'user', 'content': user_prompt},
            ],
            response_format='json_object',
            max_tokens=4096,
        )
    )
    if not result_text:
        raise RuntimeError('脚本分析失败，未返回结果')

    plan = _parse_ai_json_response(result_text)
    if not plan:
        raise RuntimeError('脚本分析结果无法解析为 JSON')
    return plan


def _image_bytes_from_gpt_result(result: dict) -> bytes:
    """从 gpt-image-2 返回结果提取图片字节。"""
    b64_data = result.get('b64_json')
    img_url = result.get('url')
    if b64_data:
        return base64.b64decode(b64_data)
    if img_url:
        import requests as _req
        r = _req.get(img_url, timeout=60)
        r.raise_for_status()
        return r.content
    raise RuntimeError('gpt-image-2 返回数据中既无 b64_json 也无 url')


def _save_image_bytes_to_media(image_bytes: bytes) -> int:
    """保存图片字节到 media 表，返回 media_id。"""
    import uuid as _uuid
    from ..media.models import MediaModel

    filename = f'script_media_{_uuid.uuid4().hex}.png'
    filepath = os.path.join(config.UPLOADS_DEFAULT_DEST, filename)
    with open(filepath, 'wb') as f:
        f.write(image_bytes)
    logger.info('生图文件已保存: %s', filename)

    with sm.transaction_scope() as sa:
        media = MediaModel.create(sa, profile={})
        media.filename = filename
        sa.flush()
        return media.id


def _generate_one_image(prompt: str, size: str) -> int:
    """调用 gpt-image-2 生成单张图并落库，返回 media_id。"""
    from ..ai.openai_api import gpt_image_2_ai

    quality = getattr(config, 'GPT_IMAGE_2_DEFAULT_QUALITY', 'high')
    result = gpt_image_2_ai.generate_image(
        prompt,
        size=size,
        quality=quality,
    )
    if not result:
        raise RuntimeError(f'gpt-image-2 生图失败: {gpt_image_2_ai.last_error}')
    image_bytes = _image_bytes_from_gpt_result(result)
    return _save_image_bytes_to_media(image_bytes)


@huey.task()
def generate_script_media_task(script_media_id: int):
    """异步生成脚本 AI 素材：先 GPT 分析规划，再 gpt-image-2 生图。"""
    from .models import ScriptMedia, Script
    from .constants import ScriptMediaStatus, ScriptMediaType

    logger.info('开始生成脚本素材: script_media_id=%s', script_media_id)

    with sm.transaction_scope() as sa:
        sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
        sm_obj.status = ScriptMediaStatus.PROCESSING.value

    try:
        with sm.transaction_scope() as sa:
            sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
            script = Script.get_or_404(sa, sm_obj.script_id)
            media_type_value = sm_obj.media_type
            custom_prompt = sm_obj.custom_prompt
            script_title = script.title or ''
            script_subtitle = script.subtitle or ''
            script_content = script.content or ''

        size_map = {
            ScriptMediaType.COVER.value: '2480x3312',
            ScriptMediaType.MATERIAL.value: '3312x2480',
        }
        size = size_map.get(media_type_value, '2048x2048')

        # 1) OpenAIGptAI 分析脚本并规划
        logger.info('调用 OpenAIGptAI 分析脚本: script_media_id=%s', script_media_id)
        plan = _plan_script_media_with_ai(
            media_type_value=media_type_value,
            title=script_title,
            subtitle=script_subtitle,
            content=script_content,
            custom_prompt=custom_prompt,
        )

        with sm.transaction_scope() as sa:
            sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
            sm_obj.ai_plan = plan

        if media_type_value == ScriptMediaType.COVER.value:
            cover_variants = [
                {
                    'segment_index': 1,
                    'segment_title': '竖版 3:4',
                    'orientation': 'portrait',
                    'size': '2480x3312',
                },
                {
                    'segment_index': 2,
                    'segment_title': '横版 4:3',
                    'orientation': 'landscape',
                    'size': '3312x2480',
                },
            ]

            with sm.transaction_scope() as sa:
                sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                sm_obj.total_segment_count = len(cover_variants)
                sm_obj.generated_items = []

            generated_items = []
            success_count = 0
            first_media_id = None
            combined_prompts = []

            for variant in cover_variants:
                image_prompt = _build_cover_image_prompt(
                    plan,
                    orientation=variant['orientation'],
                )
                if not image_prompt:
                    generated_items.append({
                        'segment_index': variant['segment_index'],
                        'segment_title': variant['segment_title'],
                        'ai_prompt': '',
                        'media_id': None,
                        'status': 'failed',
                    })
                    continue

                logger.info(
                    '生成封面: variant=%s headline=%s subline=%s prompt_prefix=%s',
                    variant['segment_title'],
                    plan.get('cover_headline'),
                    plan.get('cover_subline'),
                    image_prompt[:100],
                )
                try:
                    media_id = _generate_one_image(image_prompt, variant['size'])
                    success_count += 1
                    if first_media_id is None:
                        first_media_id = media_id
                    generated_items.append({
                        'segment_index': variant['segment_index'],
                        'segment_title': variant['segment_title'],
                        'ai_prompt': image_prompt,
                        'media_id': media_id,
                        'status': 'completed',
                    })
                    combined_prompts.append(image_prompt)
                except Exception as seg_err:
                    logger.error(
                        '封面生成失败: script_media_id=%s variant=%s err=%s',
                        script_media_id,
                        variant['segment_title'],
                        seg_err,
                    )
                    generated_items.append({
                        'segment_index': variant['segment_index'],
                        'segment_title': variant['segment_title'],
                        'ai_prompt': image_prompt,
                        'media_id': None,
                        'status': 'failed',
                    })

                with sm.transaction_scope() as sa:
                    sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                    sm_obj.generated_items = generated_items

            if success_count == 0:
                raise RuntimeError('封面两张均生成失败')

            with sm.transaction_scope() as sa:
                sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                sm_obj.media_id = first_media_id
                sm_obj.ai_prompt = '\n\n---\n\n'.join(combined_prompts)
                sm_obj.generated_items = generated_items
                sm_obj.status = ScriptMediaStatus.COMPLETED.value
                if success_count < len(cover_variants):
                    sm_obj.error_message = (
                        f'部分封面生成失败：{success_count}/{len(cover_variants)} 张成功'
                    )

            logger.info(
                '封面生成完成: script_media_id=%s success=%s/%s',
                script_media_id,
                success_count,
                len(cover_variants),
            )
            return

        # 2) 素材：按段落批量生成
        segments = plan.get('segments') or []
        if not segments:
            raise RuntimeError('素材规划未返回任何段落')

        with sm.transaction_scope() as sa:
            sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
            sm_obj.total_segment_count = len(segments)
            sm_obj.generated_items = []

        generated_items = []
        success_count = 0

        for seg in segments:
            segment_index = seg.get('segment_index') or (len(generated_items) + 1)
            segment_title = (seg.get('segment_title') or f'段落 {segment_index}').strip()
            image_prompt = _build_material_image_prompt(seg.get('image_prompt') or '')
            item = {
                'segment_index': segment_index,
                'segment_title': segment_title,
                'oral_summary': seg.get('oral_summary') or '',
                'scene_brief': seg.get('scene_brief') or '',
                'ai_prompt': image_prompt,
                'media_id': None,
                'status': 'pending',
            }

            if not image_prompt:
                item['status'] = 'failed'
                item['error_message'] = '该段落缺少 image_prompt'
                generated_items.append(item)
                with sm.transaction_scope() as sa:
                    sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                    sm_obj.generated_items = list(generated_items)
                continue

            try:
                logger.info(
                    '生成素材段落 %s/%s: %s',
                    len(generated_items) + 1,
                    len(segments),
                    segment_title[:40],
                )
                media_id = _generate_one_image(image_prompt, size)
                item['media_id'] = media_id
                item['status'] = 'completed'
                success_count += 1
            except Exception as seg_exc:
                logger.warning('段落生图失败: %s err=%s', segment_title, seg_exc)
                item['status'] = 'failed'
                item['error_message'] = str(seg_exc)[:300]

            generated_items.append(item)
            with sm.transaction_scope() as sa:
                sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                sm_obj.generated_items = list(generated_items)
                if success_count == 1 and item.get('media_id'):
                    sm_obj.media_id = item['media_id']
                    sm_obj.ai_prompt = image_prompt

        if success_count == 0:
            raise RuntimeError('所有段落素材生成均失败')

        with sm.transaction_scope() as sa:
            sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
            sm_obj.status = ScriptMediaStatus.COMPLETED.value
            if success_count < len(segments):
                sm_obj.error_message = f'部分段落生成失败：成功 {success_count}/{len(segments)}'

        logger.info(
            '素材批次生成完成: script_media_id=%s success=%s/%s',
            script_media_id,
            success_count,
            len(segments),
        )

    except Exception as exc:
        logger.exception('脚本素材生成失败: script_media_id=%s err=%s', script_media_id, exc)
        try:
            with sm.transaction_scope() as sa:
                sm_obj = ScriptMedia.get_or_404(sa, script_media_id)
                sm_obj.status = ScriptMediaStatus.FAILED.value
                sm_obj.error_message = str(exc)[:500]
        except Exception:
            logger.exception('更新失败状态时出错: script_media_id=%s', script_media_id)
