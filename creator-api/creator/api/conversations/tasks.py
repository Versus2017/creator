"""
对话相关后台任务
"""
import logging
import asyncio
import json
import os
from datetime import datetime

from ...huey_config import huey
from ...db import sm
from ...config import config
from .models import Message, Conversation, ScriptResearch, Script, UserStyleProfile
from .constants import TranscriptionStatus, RefinementStatus, ResearchStatus
from .prompts import (
    get_refinement_prompt,
    get_research_analysis_prompt,
    get_research_summary_prompt,
    get_style_profile_update_prompt,
)
from .whisper_service import get_whisper_service
from ..media.models import MediaModel
from ..ai.openai_api import ali_chat_ai, deepseek_ai

logger = logging.getLogger(__name__)


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
        
        # 5. 自动触发整理任务
        refine_transcription_task(message_id)
        
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
            ali_chat_ai(
                messages=[{'role': 'user', 'content': analysis_prompt}],
                system_prompt="你是一个专业的内容分析专家。"
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
            ali_chat_ai(
                messages=[{'role': 'user', 'content': summary_prompt}],
                system_prompt="你是一个专业的内容总结专家。"
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
            ali_chat_ai(
                messages=[{'role': 'user', 'content': update_prompt}],
                system_prompt="你是一个专业的用户画像分析师。"
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
            ali_chat_ai(
                messages=[{'role': 'user', 'content': patterns_prompt}],
                system_prompt="你是一个专业的内容模式识别专家。"
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
