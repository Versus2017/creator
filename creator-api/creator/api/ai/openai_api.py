import logging
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
from typing import Dict, Any
from ...config import config


logger = logging.getLogger(__name__)


class BaseAI:
    def __init__(self, api_key, base_url):
        self.model_name = None
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)


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


class DeepSeekAI(BaseAI):
    """DeepSeek AI模型 - 使用OpenAI SDK"""
    
    def __init__(self):
        super().__init__(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model_name = "deepseek-chat"
        self.reply = None
    
    async def reply_text(self, messages, user=None, response_format='text'):
        """
        使用DeepSeek模型回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            response_format (str): 响应格式 - 'text' 或 'json_object'
            
        Returns:
            str: AI回复内容
        """
        resp_format = {"type": 'text'} if response_format == 'text' else {"type": 'json_object'}
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                top_p=1,
                extra_body={
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
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"DeepSeek AI调用失败: {str(e)}")
            return None
    
    async def reply_stream_text(self, messages, user=None):
        """
        使用DeepSeek模型流式回复文本问题
        
        Args:
            messages (list): OpenAI格式的消息列表
            user: 用户对象
            
        Yields:
            str: SSE格式的流式数据
        """
        try:
            yield 'data:{}\n\n'.format(
                json.dumps(dict(type='start'))
            )
            
            response = await self.client.with_options(max_retries=3).chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=config.GPT_MAX_OUTPUT_TOKENS,
                top_p=1,
                extra_body={
                    "enable_search": True,
                    "search_options": {
                        "search_strategy": "turbo"
                    }
                },
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True,
                timeout=100,
                user=user.mobile if user else None
            )
            
            self.reply = ""
            
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


class DouBao16AI:
    """豆包1.6深度思考模型 - 支持深度思考能力，使用OpenAI SDK"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.DOUBAO_16_API_KEY,
            base_url=config.DOUBAO_API_URL,
            timeout=config.DOUBAO_16_TIMEOUT
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
                finish_reason = reply.choices[0].finish_reason
                delta = reply.choices[0].delta
                
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
