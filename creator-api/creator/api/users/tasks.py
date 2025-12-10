import logging
import json
import asyncio
from huey import crontab

from ...db import sm
from ...huey_config import huey
from .models import User
from ..conversations.prompts import get_user_profile_analysis_prompt
from ...config import config
from ..ai.openai_api import ali_chat_ai, doubao_16_ai

logger = logging.getLogger(__name__)

@huey.task()
def analyze_user_profile(user_id: int):
    """
    异步任务：分析用户简介，生成画像（总结+标签）
    """
    logger.info(f"Start analyzing profile for user {user_id}")
    
    with sm.transaction_scope() as sa:
        user = User.get_or_404(sa, user_id)
        introduction = user.introduction
        
        if not introduction:
            logger.warning(f"User {user_id} has no introduction, skip analysis.")
            return

        try:
            # 1. 获取提示词
            prompt = get_user_profile_analysis_prompt(introduction)
            messages = [{"role": "user", "content": prompt}]
            
            # 2. 调用AI服务 (使用阿里模型，支持JSON模式)
            logger.info("Calling AI service for profile analysis...")
            
            # 使用 asyncio.run 调用异步函数（与 conversations/tasks.py 保持一致）
            ai_response_text = asyncio.run(
                ali_chat_ai.reply_text(
                    messages=messages, 
                    user=user,
                    response_format='json'
                )
            )
            
            if not ai_response_text:
                logger.error("AI service returned empty response")
                return

            # 3. 解析返回结果
            try:
                # 清理可能的 markdown 标记 (```json ... ```)
                cleaned_text = ai_response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                ai_result = json.loads(cleaned_text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {ai_response_text[:500]}")
                # 兜底尝试：如果是普通文本，返回降级结果
                return
            
            # 4. 更新用户画像
            if ai_result:
                # 验证字段是否存在
                summary = ai_result.get('ai_summary')
                tags = ai_result.get('tags', [])
                
                # 简单清洗 tags，确保是列表且元素为字符串
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',')]
                elif isinstance(tags, list):
                    tags = [str(t).strip() for t in tags]
                
                if summary:
                    user.ai_summary = summary
                if tags:
                    user.tags = tags[:5]  # 限制最多5个
                
                logger.info(f"Updated profile for user {user_id}: summary={summary[:50]}..., tags={tags}")
            
        except Exception as e:
            logger.error(f"Error analyzing profile for user {user_id}: {e}", exc_info=True)
