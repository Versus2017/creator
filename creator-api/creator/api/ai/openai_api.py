import logging
import re
import uuid
import httpx
import openai
from openai import OpenAI, AsyncOpenAI
import time
import json
import requests
import base64
from pathlib import Path
import io
from typing import Dict, Any, Optional
from ...config import config


logger = logging.getLogger(__name__)


def _make_async_openai_client(api_key: str, base_url: str, timeout: Optional[float] = 100):
    """
    创建 OpenAI 异步客户端。
    trust_env=False：不读取系统 HTTP_PROXY/HTTPS_PROXY（避免走 Clash 127.0.0.1:7897 等）。
    若需代理，仅在 config.GPT_PROXY 显式配置时启用。
    """
    proxy = (config.GPT_PROXY or '').strip()
    if proxy:
        http_client = httpx.AsyncClient(proxy=proxy, timeout=timeout)
        logger.info('AI HTTP 使用配置代理: %s', proxy)
    else:
        http_client = httpx.AsyncClient(trust_env=False, timeout=timeout)
    return AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


class BaseAI:
    def __init__(self, api_key, base_url, timeout: Optional[float] = 100):
        self.model_name = None
        self.client = _make_async_openai_client(api_key, base_url, timeout=timeout)


class AliChatAI(BaseAI):
    def __init__(self):
        super().__init__(
            api_key=config.ALY_MODEL_API_KEY,
            base_url=config.ALY_API_URL
        )
        self.model_name = config.ALY_MODEL_NAME
        self.reply = ""

    async def reply_text(self, messages, user=None, response_format='text', max_tokens=None):
        resp_format = {"type": 'text'} if response_format == 'text' else {"type": 'json_object'}
        try:
            finish_reason = None
            # 如果没有指定max_tokens，使用配置的默认值
            tokens = max_tokens if max_tokens is not None else config.GPT_MAX_OUTPUT_TOKENS
            while finish_reason is None or finish_reason == "tool_calls":
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=tokens,
                    top_p=1,
                    extra_body={
                        "enable_thinking": True,
                        "thinking_budget": 50,
                        "enable_search": True,
                        "search_options": {
                            "search_strategy": "turbo"
                        }
                    },
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    response_format=resp_format,
                    stream=False,
                    timeout=100,
                    user=user.mobile if user else None,
                )
                choice = response.choices[0]
                finish_reason = choice.finish_reason
                logger.warning(f'finish_reason: {finish_reason}')
                if finish_reason == "tool_calls":
                    messages.append(choice.message)
            if choice and choice.message:
                content = choice.message.content
                return content
        except Exception as e:
            logger.warning(e)
            return None

    async def reply_stream_text(self, query, user):
        try:
            logger.warning(
                "AliChat 流式调用 model=%s（创作对话应走 DeepSeek，请检查调用栈）",
                self.model_name,
            )
            # 重置回复内容
            self.reply = ""
            
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='start'))
            )
            response = await self.client.with_options(max_retries=3).chat.completions.create(
                model=self.model_name,
                messages=query,
                temperature=0.5,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                top_p=1,
                extra_body={
                    "enable_thinking": True,
                    "thinking_budget": 50,
                    "enable_search": True,
                    "search_options": {
                        "search_strategy": "turbo"
                    }
                },
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True,
                timeout=30,
                user=user.mobile if user else None
            )
            async for reply in response:
                finish_reason = reply.choices[0].finish_reason
                content = reply.choices[0].delta.content or ""
                if finish_reason == 'content_filter':
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='stop', content='内容不合法')))
                    break
                if finish_reason == 'length':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if finish_reason == 'stop':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if content is None:
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='begin')))
                    continue
                self.reply = self.reply + content
                yield 'data:{}\n\n'.format(
                    json.dumps(dict(type='input', content=content))
                )
        except openai.RateLimitError as e:
            logger.warning(e)
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error',
                                content='提问太快啦，请休息一下再问我吧~'))
            )
        except openai.APIConnectionError as e:
            logger.warning(e)
            logger.warning("[CHATGPT] APIConnection failed")
            yield 'data:{}\n\n'.format(
                json.dumps(
                    dict(type='error', content='链接失败，请重试'))
            )
        except Exception as e:
            logger.warning(e)
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', extra='unknown',
                                content='请再问我一次吧~'))
            )


class DouBaoVisionAI(BaseAI):
    """豆包视觉理解AI - 支持图片识别和分析"""
    
    def __init__(self):
        super().__init__(
            api_key=config.DOUBAO_API_KEY,
            base_url=config.DOUBAO_API_URL
        )
        self.model_name = config.DOUBAO_VISION_MODEL
    
    def _get_image_base64_from_file(self, filename):
        """
        从服务器本地文件获取图片的base64编码
        
        Args:
            filename (str): 文件名
            
        Returns:
            str: base64编码的图片数据，格式为 "data:image/jpeg;base64,..."
        """
        try:
            import os
            file_path = os.path.join(config.UPLOADS_DEFAULT_DEST, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                
                # 根据文件扩展名确定MIME类型
                file_ext = filename.lower().split('.')[-1]
                mime_type_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp'
                }
                mime_type = mime_type_map.get(file_ext, 'image/jpeg')
                
                return f"data:{mime_type};base64,{encoded_image}"
                
        except Exception as e:
            logger.error(f"Error reading image file {filename}: {e}")
            return None
    
    async def reply_with_vision(self, messages, image_filenames=None, user=None):
        """
        使用视觉模型分析图片并回复（非流式）
        
        Args:
            messages (list): OpenAI格式的消息列表
            image_filenames (list): 图片文件名列表
            user: 用户对象
            
        Returns:
            str: AI回复内容
        """
        try:
            # 如果有图片，将图片添加到最后一条用户消息中
            if image_filenames and len(image_filenames) > 0:
                # 找到最后一条用户消息
                last_user_msg_idx = None
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get('role') == 'user':
                        last_user_msg_idx = i
                        break
                
                if last_user_msg_idx is not None:
                    # 构建包含图片的消息内容
                    content_parts = []
                    
                    # 添加文本部分
                    original_content = messages[last_user_msg_idx].get('content', '')
                    if isinstance(original_content, str):
                        content_parts.append({
                            "type": "text",
                            "text": original_content
                        })
                    
                    # 添加图片部分
                    for filename in image_filenames:
                        image_base64 = self._get_image_base64_from_file(filename)
                        if image_base64:
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": image_base64
                                }
                            })
                    
                    # 更新消息内容为多模态格式
                    messages[last_user_msg_idx]['content'] = content_parts
            
            # 调用豆包视觉模型
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                extra_body={
                    "enable_search": True,
                    "search_options": {
                        "search_strategy": "turbo"
                    }
                },
                stream=False,
                timeout=120,
                user=user.mobile if user else None,
            )
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"豆包视觉AI调用失败: {str(e)}")
            return None
    
    async def reply_with_vision_stream(self, messages, image_filenames=None, user=None):
        """
        使用视觉模型分析图片并流式回复
        
        Args:
            messages (list): OpenAI格式的消息列表
            image_filenames (list): 图片文件名列表
            user: 用户对象
            
        Yields:
            str: SSE格式的流式数据
        """
        try:
            # 如果有图片，将图片添加到最后一条用户消息中
            if image_filenames and len(image_filenames) > 0:
                # 找到最后一条用户消息
                last_user_msg_idx = None
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get('role') == 'user':
                        last_user_msg_idx = i
                        break
                
                if last_user_msg_idx is not None:
                    # 构建包含图片的消息内容
                    content_parts = []
                    
                    # 添加文本部分
                    original_content = messages[last_user_msg_idx].get('content', '')
                    if isinstance(original_content, str):
                        content_parts.append({
                            "type": "text",
                            "text": original_content
                        })
                    
                    # 添加图片部分
                    for filename in image_filenames:
                        image_base64 = self._get_image_base64_from_file(filename)
                        if image_base64:
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": image_base64
                                }
                            })
                    
                    # 更新消息内容为多模态格式
                    messages[last_user_msg_idx]['content'] = content_parts
            
            # 发送开始事件
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='start'))
            )
            
            # 调用豆包视觉模型（流式）
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                extra_body={
                    "enable_search": True,
                    "search_options": {
                        "search_strategy": "turbo"
                    }
                },
                stream=True,
                timeout=120,
                user=user.mobile if user else None,
            )
            
            full_content = ""
            
            async for chunk in response:
                finish_reason = chunk.choices[0].finish_reason
                content = chunk.choices[0].delta.content or ""
                
                if finish_reason == 'content_filter':
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='stop', content='内容不合法')))
                    break
                if finish_reason == 'length':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if finish_reason == 'stop':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if content is None:
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='begin')))
                    continue
                
                full_content += content
                yield 'data:{}\n\n'.format(
                    json.dumps(dict(type='input', content=content))
                )
            
            # 流式结束后，返回完整内容（供外部使用）
            self.last_reply = full_content
                
        except openai.RateLimitError as e:
            logger.error(f"豆包视觉AI限流错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error',
                                content='提问太快啦，请休息一下再问我吧~'))
            )
        except openai.APIConnectionError as e:
            logger.error(f"豆包视觉AI连接错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(
                    dict(type='error', content='连接失败，请重试'))
            )
        except Exception as e:
            logger.error(f"豆包视觉AI流式调用失败: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', extra='unknown',
                                content='图片识别失败，请重试'))
            )


def _extract_assistant_text(message) -> str:
    """只取用户可见正文，排除 deepseek-v4-pro 等模型的 reasoning_content。"""
    if not message:
        return ''
    return getattr(message, 'content', None) or ''


def _resolve_api_user(user=None, user_mobile=None):
    """安全解析 OpenAI API 的 user 字段，避免 detached ORM 对象。"""
    if user_mobile:
        return user_mobile
    if user is None:
        return None
    try:
        return user.mobile
    except Exception:
        return getattr(user, 'mobile', None)


class DeepSeekAI(BaseAI):
    """DeepSeek AI模型 - 使用OpenAI SDK"""
    
    def __init__(self):
        super().__init__(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
        self.model_name = config.DEEPSEEK_MODEL_NAME
        self.reply = None
    
    async def reply_text(self, messages, user=None, user_mobile=None, response_format='text', max_tokens=None):
        """
        使用DeepSeek模型回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            user_mobile: 用户标识（优先，避免 ORM detached）
            response_format (str): 响应格式 - 'text' 或 'json_object'
            max_tokens: 最大输出 token，默认使用配置值
            
        Returns:
            str: AI回复内容
        """
        resp_format = {"type": 'text'} if response_format == 'text' else {"type": 'json_object'}
        tokens = max_tokens if max_tokens is not None else config.GPT_MAX_OUTPUT_TOKENS
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=tokens,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                response_format=resp_format,
                stream=False,
                timeout=100,
                user=_resolve_api_user(user, user_mobile),
            )
            
            if response.choices and response.choices[0].message:
                text = _extract_assistant_text(response.choices[0].message)
                return text or None
            
            return None
            
        except Exception as e:
            logger.error(f"DeepSeek AI调用失败: {str(e)}")
            return None
    
    async def reply_stream_text(self, messages, user=None, user_mobile=None):
        """
        使用DeepSeek模型流式回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            
        Yields:
            str: SSE格式的流式数据
        """
        try:
            logger.info(
                "DeepSeek 流式调用 model=%s base_url=%s",
                self.model_name,
                str(self.client.base_url),
            )
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='start'))
            )
            
            response = await self.client.with_options(max_retries=3).chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True,
                timeout=100,
                user=_resolve_api_user(user, user_mobile),
            )
            
            self.reply = ""
            
            async for reply in response:
                if not reply.choices:
                    continue
                choice = reply.choices[0]
                finish_reason = choice.finish_reason
                delta = choice.delta
                if delta is None:
                    if finish_reason in ('stop', 'length', 'content_filter'):
                        if finish_reason == 'content_filter':
                            yield 'data:{}\n\n'.format(
                                json.dumps(dict(type='stop', content='内容不合法')))
                        else:
                            yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                        break
                    continue
                # deepseek-v4-pro：先 reasoning_content（思考），再 content（正文）
                # 思考不落库、不拼进 message.content，与豆包1.6 一致走 type=thinking
                reasoning = getattr(delta, 'reasoning_content', None) or ''
                content = delta.content if delta.content is not None else ''
                
                if finish_reason == 'content_filter':
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='stop', content='内容不合法')))
                    break
                if finish_reason == 'length':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if finish_reason == 'stop':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break

                if reasoning:
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='thinking', content=reasoning))
                    )
                if content:
                    self.reply = self.reply + content
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='input', content=content))
                    )
                
        except openai.RateLimitError as e:
            logger.error(f"DeepSeek限流错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error',
                                content='提问太快啦，请休息一下再问我吧~'))
            )
        except openai.APIConnectionError as e:
            logger.error(f"DeepSeek连接错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(
                    dict(type='error', content='链接失败，请重试'))
            )
        except Exception as e:
            logger.error(f"DeepSeek流式调用失败: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', extra='unknown',
                                content='请再问我一次吧~'))
            )


class OpenAIGptAI(BaseAI):
    """OpenAI 兼容创作对话（laozhang.ai 等），流式仅 content，无 reasoning_content。"""

    def __init__(self):
        super().__init__(
            api_key=config.OPENAI_GPT_API_KEY,
            base_url=config.OPENAI_GPT_API_BASE,
        )
        self.model_name = config.OPENAI_GPT_MODEL_NAME
        self.reply = ""

    def _output_tokens(self, max_tokens=None) -> int:
        tokens = max_tokens if max_tokens is not None else config.GPT_MAX_OUTPUT_TOKENS
        return max(int(tokens), 16)

    def _uses_max_completion_tokens(self) -> bool:
        """GPT-5 / o 系列走 max_completion_tokens，不再接受 max_tokens。"""
        name = (self.model_name or '').lower()
        return (
            name.startswith('gpt-5')
            or name.startswith('o1')
            or name.startswith('o3')
            or name.startswith('o4')
        )

    def _completion_limit_kwargs(self, tokens: int) -> dict:
        if self._uses_max_completion_tokens():
            return {'extra_body': {'max_completion_tokens': tokens}}
        return {'max_tokens': tokens}

    async def reply_text(self, messages, user=None, user_mobile=None, response_format='text', max_tokens=None):
        resp_format = {"type": 'text'} if response_format == 'text' else {"type": 'json_object'}
        tokens = self._output_tokens(max_tokens)
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                response_format=resp_format,
                stream=False,
                timeout=100,
                user=_resolve_api_user(user, user_mobile),
                **self._completion_limit_kwargs(tokens),
            )
            if response.choices and response.choices[0].message:
                text = _extract_assistant_text(response.choices[0].message)
                return text or None
            return None
        except Exception as e:
            logger.error(f"OpenAI GPT 调用失败: {str(e)}")
            return None

    async def reply_stream_text(self, messages, user=None, user_mobile=None):
        try:
            tokens = self._output_tokens(None)
            limit_param = 'max_completion_tokens' if self._uses_max_completion_tokens() else 'max_tokens'
            logger.info(
                "OpenAI GPT 流式调用 model=%s base_url=%s %s=%s",
                self.model_name,
                str(self.client.base_url),
                limit_param,
                tokens,
            )
            yield 'data:{}\n\n'.format(json.dumps(dict(type='start')))

            response = await self.client.with_options(max_retries=3).chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True,
                timeout=100,
                user=_resolve_api_user(user, user_mobile),
                **self._completion_limit_kwargs(tokens),
            )

            self.reply = ""

            async for reply in response:
                if not reply.choices:
                    continue
                choice = reply.choices[0]
                finish_reason = choice.finish_reason
                delta = choice.delta
                content = ''
                if delta is not None:
                    content = delta.content if delta.content is not None else ''

                if finish_reason == 'content_filter':
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='stop', content='内容不合法')))
                    break
                if finish_reason == 'length':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if finish_reason == 'stop':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if not content:
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='begin')))
                    continue

                self.reply = self.reply + content
                yield 'data:{}\n\n'.format(
                    json.dumps(dict(type='input', content=content))
                )

        except openai.RateLimitError as e:
            logger.error(f"OpenAI GPT 限流错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', content='提问太快啦，请休息一下再问我吧~'))
            )
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI GPT 连接错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', content='链接失败，请重试'))
            )
        except Exception as e:
            logger.error(f"OpenAI GPT 流式调用失败: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', extra='unknown', content='请再问我一次吧~'))
            )


class DouBao16AI:
    """豆包1.6深度思考模型 - 支持深度思考能力，使用OpenAI SDK"""
    
    def __init__(self):
        self.client = _make_async_openai_client(
            config.DOUBAO_16_API_KEY,
            config.DOUBAO_API_URL,
            timeout=config.DOUBAO_16_TIMEOUT,
        )
        self.model_name = config.DOUBAO_16_MODEL
        self.thinking_mode = config.DOUBAO_16_THINKING_MODE
        self.reply = ""  # 初始化回复内容
        self.reasoning = ""  # 初始化思考内容
    
    async def reply_text(self, messages, user=None, thinking_mode=None):
        """
        使用豆包1.6模型回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            thinking_mode (str): 思考模式 - 'disabled'(不使用), 'enabled'(使用), 'auto'(自动判断)
                               如果不传，使用配置的默认模式
            
        Returns:
            str: AI回复内容
        """
        try:
            # 确定思考模式
            mode = thinking_mode if thinking_mode else self.thinking_mode
            
            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": messages,
            }
            
            # 构建 extra_body，包含 thinking 和 search 配置
            extra_body_config = {
                "enable_search": True,
                "search_options": {
                    "search_strategy": "turbo"
                }
            }
            
            # 添加 thinking 参数到 extra_body（如果需要）
            if mode and mode != 'disabled':
                extra_body_config["thinking"] = {
                    "type": mode
                }
            
            params["extra_body"] = extra_body_config
            
            # 调用豆包1.6模型
            response = await self.client.chat.completions.create(**params)
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"豆包1.6深度思考AI调用失败: {str(e)}")
            return None
    
    async def reply_stream_text(self, messages, user=None, thinking_mode=None, max_tokens=None):
        """
        使用豆包1.6模型流式回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            thinking_mode (str): 思考模式 - 'disabled'(不使用), 'enabled'(使用), 'auto'(自动判断)
            max_tokens (int): 最大输出token数，如果不传则使用配置的默认值
            
        Yields:
            str: SSE格式的流式数据
        """
        try:
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='start'))
            )
            
            # 确定思考模式
            mode = thinking_mode if thinking_mode else self.thinking_mode
            
            # 确定最大token数
            tokens = max_tokens if max_tokens else config.GPT_MAX_OUTPUT_TOKENS

            logger.info(f"****************豆包1.6深度思考模型 - 最大输出token数: {tokens}")
            
            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": tokens,
                "top_p": 1,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stream": True,
                "timeout": 120,
                "user": user.mobile or user.nickname if user else None
            }
            
            # 构建 extra_body，包含 thinking 和 search 配置
            extra_body_config = {
                "enable_search": True,
                "search_options": {
                    "search_strategy": "turbo"
                }
            }
            
            # 添加 thinking 参数到 extra_body（如果需要）
            if mode and mode != 'disabled':
                extra_body_config["thinking"] = {
                    "type": mode
                }
            
            params["extra_body"] = extra_body_config
            
            # 调用豆包1.6模型（流式）
            response = await self.client.with_options(max_retries=3).chat.completions.create(**params)
            
            # 累积完整响应
            self.reply = ""
            self.reasoning = ""  # 累积思考内容
            
            async for reply in response:
                if not reply.choices:
                    continue
                finish_reason = reply.choices[0].finish_reason
                delta = reply.choices[0].delta
                if delta is None:
                    if finish_reason in ('stop', 'length', 'content_filter'):
                        if finish_reason == 'content_filter':
                            yield 'data:{}\n\n'.format(
                                json.dumps(dict(type='stop', content='内容不合法')))
                        else:
                            yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                        break
                    continue
                
                # 检查是否有思考内容（豆包1.6深度思考特性）
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_content = delta.reasoning_content
                    self.reasoning += reasoning_content
                    # 发送思考过程给前端
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='thinking', content=reasoning_content))
                    )
                
                # 处理正常回复内容
                content = delta.content or ""
                
                if finish_reason == 'content_filter':
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='stop', content='内容不合法')))
                    break
                if finish_reason == 'length':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if finish_reason == 'stop':
                    yield 'data:{}\n\n'.format(json.dumps(dict(type='stop')))
                    break
                if content is None or content == "":
                    yield 'data:{}\n\n'.format(
                        json.dumps(dict(type='begin')))
                    continue
                
                self.reply = self.reply + content
                yield 'data:{}\n\n'.format(
                    json.dumps(dict(type='input', content=content))
                )
                
        except openai.RateLimitError as e:
            logger.error(f"豆包1.6限流错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error',
                                content='提问太快啦，请休息一下再问我吧~'))
            )
        except openai.APIConnectionError as e:
            logger.error(f"豆包1.6连接错误: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(
                    dict(type='error', content='链接失败，请重试'))
            )
        except Exception as e:
            logger.error(f"豆包1.6流式调用失败: {str(e)}")
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='error', extra='unknown',
                                content='请再问我一次吧~'))
            )
    
    async def reply_with_vision(self, messages, image_url=None, user=None, thinking_mode=None):
        """
        使用豆包1.6模型进行图片分析并回复
        
        Args:
            messages (list): OpenAI格式的消息列表
            image_url (str): 图片URL地址
            user: 用户对象
            thinking_mode (str): 思考模式
            
        Returns:
            str: AI回复内容
        """
        try:
            # 如果有图片，将图片添加到最后一条用户消息中
            if image_url:
                # 找到最后一条用户消息
                last_user_msg_idx = None
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get('role') == 'user':
                        last_user_msg_idx = i
                        break
                
                if last_user_msg_idx is not None:
                    # 构建包含图片的消息内容
                    original_content = messages[last_user_msg_idx].get('content', '')
                    content_parts = []
                    
                    # 添加文本部分
                    if isinstance(original_content, str):
                        content_parts.append({
                            "type": "text",
                            "text": original_content
                        })
                    
                    # 添加图片部分
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    })
                    
                    # 更新消息内容为多模态格式
                    messages[last_user_msg_idx]['content'] = content_parts
            
            # 调用模型（图片分析）
            return await self.reply_text(messages, user, thinking_mode)
            
        except Exception as e:
            logger.error(f"豆包1.6视觉AI调用失败: {str(e)}")
            return None


ali_chat_ai = AliChatAI()
doubao_vision_ai = DouBaoVisionAI()
doubao_16_ai = DouBao16AI()
deepseek_ai = DeepSeekAI()
openai_gpt_ai = OpenAIGptAI()


def normalize_model_type(model_type: Optional[str] = None) -> str:
    """统一 model_type，默认 deepseek。"""
    if model_type is None or (isinstance(model_type, str) and not model_type.strip()):
        return 'deepseek'
    return str(model_type).strip()


def resolve_conversation_model_type(request_model_type: Optional[str] = None) -> str:
    """创作对话实际使用的 model_type（默认读 config，可选允许请求覆盖）。"""
    if config.CHAT_ALLOW_REQUEST_MODEL_OVERRIDE and request_model_type:
        return normalize_model_type(request_model_type)
    return normalize_model_type(config.CHAT_CONVERSATION_MODEL_TYPE)


def resolve_codex_model_type() -> str:
    return normalize_model_type(config.CHAT_CODEX_MODEL_TYPE)


def resolve_script_media_plan_model_type() -> str:
    return normalize_model_type(config.CHAT_SCRIPT_MEDIA_PLAN_MODEL_TYPE)


def get_chat_ai_model(model_type: Optional[str] = None):
    """按 model_type 选择对话模型，默认 DeepSeek。"""
    model_type = normalize_model_type(model_type)
    if model_type == 'ali_chat':
        return ali_chat_ai
    if model_type == 'doubao_vision':
        return doubao_vision_ai
    if model_type == 'doubao_16':
        return doubao_16_ai
    if model_type == 'openai_gpt':
        return openai_gpt_ai
    return deepseek_ai


async def reply_stream_text_default(messages, user=None):
    """流式对话默认 DeepSeek，不自动降级千问（避免误用通义）。"""
    async for chunk in deepseek_ai.reply_stream_text(messages, user):
        yield chunk


async def reply_text_default(messages, user=None, response_format='text', max_tokens=None):
    """默认 DeepSeek 非流式回复，失败或空结果时降级通义千问。"""
    try:
        result = await deepseek_ai.reply_text(
            messages=messages,
            user=user,
            response_format=response_format,
            max_tokens=max_tokens,
        )
        if result:
            return result
    except Exception as e:
        logger.warning(f"DeepSeek 调用失败，降级通义千问: {e}")
    return await ali_chat_ai.reply_text(
        messages=messages,
        user=user,
        response_format=response_format,
        max_tokens=max_tokens,
    )


# GPTImage2 Enterprise / Sora2Official 官方兼容线路允许的 size
GPT_IMAGE_2_VIP_SIZES = frozenset({"1024x1024", "1536x1024", "1024x1536", "2048x2048", "2048x1152", "auto"})


def normalize_gpt_image_vip_size(size: Optional[str], *, default: str = "2048x2048") -> str:
    """将 WxH / 2K / 4K 等映射到 gpt-image-2-vip 支持的 size。"""
    raw = (size or "").strip()
    if not raw:
        return default
    low = raw.lower()
    if low == "auto":
        return "auto"
    tok_up = raw.upper()
    if tok_up == "2K":
        return "2048x1152"
    if tok_up == "4K":
        return "2048x2048"
    if low in GPT_IMAGE_2_VIP_SIZES:
        return low
    m = re.match(r"^(\d{2,5})\s*[xX]\s*(\d{2,5})$", raw)
    if m:
        token = f"{int(m.group(1))}x{int(m.group(2))}"
        if token in GPT_IMAGE_2_VIP_SIZES:
            return token
        w, h = int(m.group(1)), int(m.group(2))
        aspect = (float(w) / float(h)) if h else 1.0
        if aspect >= 1.25:
            return "2048x1152"
        if aspect <= 0.82:
            return "1024x1536"
        return "2048x2048"
    return default


def gpt_image_2_http_timeout(seconds: Optional[int] = None) -> int:
    """老张 gpt-image 线路 requests 超时（秒）。不传则用配置值。"""
    if seconds is not None:
        return max(30, int(seconds))
    try:
        cfg = int(getattr(config, "GPT_IMAGE_2_REQUEST_TIMEOUT", 240) or 240)
    except (TypeError, ValueError):
        cfg = 240
    return max(30, cfg)


class GPTImage2AI:
    """老张 API GPT Image 2 图片生成客户端（同步，供 Huey 任务使用）"""

    VIP_SIZES = GPT_IMAGE_2_VIP_SIZES
    OFFICIAL_SIZES = VIP_SIZES | {
        "3840x2160", "2160x3840",
        # 4K 常用比例
        "2880x2880",  # 1:1
        "2336x3520",  # 2:3
        "3520x2336",  # 3:2
        "2480x3312",  # 3:4
        "3312x2480",  # 4:3
        "2560x3216",  # 4:5
        "3216x2560",  # 5:4
        "2160x3840",  # 9:16
        "3840x1632",  # 21:9
    }
    OFFICIAL_QUALITIES = {"low", "medium", "high", "auto"}

    def __init__(self):
        self.base_url = (getattr(config, "GPT_IMAGE_2_API_URL", "") or "https://api.laozhang.ai/v1").rstrip("/")
        self.api_key = (getattr(config, "GPT_IMAGE_2_API_KEY", "") or "").strip()
        self.model_name = (getattr(config, "GPT_IMAGE_2_MODEL_NAME", "") or "gpt-image-2").strip()
        self.route = (getattr(config, "GPT_IMAGE_2_ROUTE", "") or "enterprise").strip().lower()
        self.last_error: Optional[str] = None
        self.last_request_payload: Optional[Dict[str, Any]] = None

    def _build_payload(self, prompt: str, size: Optional[str] = None, quality: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
        }
        route = self.route
        size_value = (size or "").strip()
        quality_value = (quality or "").strip().lower()

        if route == "vip":
            if size_value in self.VIP_SIZES:
                payload["size"] = size_value
        elif route in ("sora2official", "enterprise"):
            if size_value in self.OFFICIAL_SIZES:
                payload["size"] = size_value
            if quality_value in self.OFFICIAL_QUALITIES:
                payload["quality"] = quality_value
        return payload

    @staticmethod
    def _normalize_b64_json(value: str) -> Optional[str]:
        text = (value or "").strip()
        if not text:
            return None
        if text.startswith("data:"):
            text = text.split(",", 1)[1]
        text += "=" * ((4 - len(text) % 4) % 4)
        return text

    def generate_image(
        self,
        prompt: str,
        *,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """生成图片，返回包含 url / b64_json 的 dict，失败返回 None。"""
        p = (prompt or "").strip()
        if not p:
            return None
        if not self.api_key:
            self.last_error = "GPT_IMAGE_2_API_KEY is empty"
            logger.warning(self.last_error)
            return None

        payload = self._build_payload(p, size=size, quality=quality)
        self.last_request_payload = dict(payload)
        try:
            self.last_error = None
            tout = gpt_image_2_http_timeout(timeout)
            resp = requests.post(
                f"{self.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=tout,
            )
            if resp.status_code >= 400:
                self.last_error = resp.text
                logger.warning("[gpt-image-2] failed status=%s body=%s", resp.status_code, resp.text)
                return None
            data = resp.json()
            rows = data.get("data") or []
            first = rows[0] if rows else {}
            url = (first.get("url") or "").strip()
            b64_json = self._normalize_b64_json(first.get("b64_json") or "")
            if not url and not b64_json:
                self.last_error = "empty image payload"
                logger.warning("[gpt-image-2] empty payload: %s", data)
                return None
            return dict(
                url=url or None,
                b64_json=b64_json,
                model_name=self.model_name,
                route=self.route,
                payload=payload,
                raw=data,
            )
        except Exception as e:
            self.last_error = str(e)
            logger.warning("[gpt-image-2] exception: %s", e)
            return None

    def generate_image_url(
        self,
        prompt: str,
        *,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """生成图片并只返回 URL，失败或仅有 b64_json 时返回 None。"""
        result = self.generate_image(prompt, size=size, quality=quality, timeout=timeout)
        if not result:
            return None
        url = result.get("url")
        if not url:
            self.last_error = "image generated but URL is empty (check b64_json)"
            logger.warning("[gpt-image-2] generate_image_url: url empty")
        return url


gpt_image_2_ai = GPTImage2AI()
