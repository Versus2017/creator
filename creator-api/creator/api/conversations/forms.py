from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from ..forms import BaseFilterForm
from ...config import config


class ConversationFilterForm(BaseFilterForm):
    """会话筛选表单"""
    status: Optional[int] = None


class ConversationForm(BaseModel):
    """会话创建/编辑表单"""
    title: str = Field(..., min_length=1, max_length=200, description="会话标题")
    topic: str = Field(..., min_length=1, max_length=500, description="视频主题")


class MessageForm(BaseModel):
    """消息创建表单"""
    conversation_id: int = Field(..., description="会话ID", gt=0)
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., min_length=1, description="消息内容")
    audio_url: Optional[str] = Field(None, description="语音文件URL")
    audio_duration: Optional[int] = Field(None, description="语音时长（秒）", ge=0)


class ScriptFilterForm(BaseFilterForm):
    """脚本筛选表单"""
    status: Optional[int] = None
    format_type: Optional[str] = None
    conversation_id: Optional[int] = None


class ScriptForm(BaseModel):
    """脚本创建/编辑表单"""
    title: str = Field(..., min_length=1, max_length=200, description="脚本标题")
    subtitle: Optional[str] = Field(None, max_length=500, description="脚本副标题")
    content: str = Field(..., min_length=1, description="脚本内容（Markdown格式）")
    format_type: str = Field(default='vlog', description="格式类型")
    conversation_id: Optional[int] = Field(None, description="关联的会话ID", gt=0)


class ScriptUpdateForm(BaseModel):
    """脚本更新表单"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="脚本标题")
    content: Optional[str] = Field(None, min_length=1, description="脚本内容")
    status: Optional[int] = Field(None, description="脚本状态")
    quality_score: Optional[int] = Field(None, description="质量评分", ge=0, le=100)


class ChatStreamForm(BaseModel):
    """AI对话流式请求表单"""
    conversation_id: int = Field(..., description="会话ID", gt=0)
    content: str = Field(..., min_length=1, max_length=10000, description="用户消息内容")
    audio_url: Optional[str] = Field(None, description="语音文件URL")
    audio_duration: Optional[int] = Field(None, description="语音时长（秒）", ge=0)
    image_urls: Optional[list] = Field(None, description="图片URL列表（用于多模态）")
    model_type: Optional[str] = Field(default='deepseek', description="AI模型类型：ali_chat/deepseek/doubao_vision/doubao_16")
    thinking_mode: Optional[str] = Field(None, description="思考模式（仅豆包1.6）：disabled/enabled/auto")
    message_id: Optional[int] = Field(None, description="已存在的消息ID（如果传入，则不创建新的用户消息）", gt=0)
    referenced_script_ids: Optional[List[int]] = Field(
        None,
        description="引用的历史脚本ID列表，最多3个",
    )

    @field_validator('referenced_script_ids', mode='before')
    @classmethod
    def normalize_referenced_script_ids(cls, v):
        if v is None:
            return None
        if not isinstance(v, list):
            return None
        seen = set()
        result = []
        for item in v:
            try:
                sid = int(item)
            except (TypeError, ValueError):
                continue
            if sid <= 0 or sid in seen:
                continue
            seen.add(sid)
            result.append(sid)
            if len(result) >= config.CHAT_MAX_REFERENCED_SCRIPTS:
                break
        return result

    @field_validator('model_type', mode='before')
    @classmethod
    def normalize_model_type(cls, v):
        # JSON 传 null 时 Pydantic 不会用 Field 默认值，需显式回落到 deepseek
        if v is None or (isinstance(v, str) and not v.strip()):
            return 'deepseek'
        return str(v).strip()


class ScriptGenerateForm(BaseModel):
    """AI生成脚本表单"""
    conversation_id: int = Field(..., description="会话ID", gt=0)
    topic: str = Field(..., min_length=1, max_length=500, description="视频主题")
    format_type: str = Field(default='vlog', description="脚本格式类型")
    requirements: Optional[str] = Field(None, description="其他要求或说明")
    use_style_profile: Optional[bool] = Field(True, description="是否使用用户风格档案")
    model_type: Optional[str] = Field('deepseek', description="AI模型类型")


class VoiceMessageForm(BaseModel):
    """语音消息创建表单"""
    audio_media_id: int = Field(..., description="音频文件Media ID（通过/media接口上传获得）", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_media_id": 123
            }
        }


class VoiceStreamForm(BaseModel):
    """语音流式分块上传表单
    
    录音过程中定期上传**本段**音频切片（非累积整段），服务端追加到主文件后转写。
    - 首块（chunk_index=0, message_id=None）：自动创建 Message 并返回 message_id
    - 后续块：携带 message_id，服务端将切片追加到主录音后转写新增时段
    - 最终块（is_final=True）：触发文本合并 + 整理任务
    """
    audio_media_id: int = Field(..., description="本分块音频的 Media ID（首块即主录音）", gt=0)
    chunk_index: int = Field(..., description="块序号（0-based）", ge=0)
    message_id: Optional[int] = Field(None, description="消息ID（首块为空，后续块必填）", gt=0)
    is_final: bool = Field(False, description="是否为最终块（录音结束时为 True）")

    class Config:
        json_schema_extra = {
            "example": {
                "audio_media_id": 456,
                "chunk_index": 0,
                "message_id": None,
                "is_final": False
            }
        }


class MessageConfirmForm(BaseModel):
    """消息内容确认表单（用户确认或修改AI整理后的内容）"""
    content: str = Field(..., min_length=1, max_length=50000, description="确认或修改后的消息内容")
    send_to_ai: bool = Field(default=True, description="是否立即发送给AI进行对话")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "我想制作一个咖啡冲泡教程视频，主要讲解手冲咖啡的技巧...",
                "send_to_ai": True
            }
        }


class MessageRetryForm(BaseModel):
    """消息重试表单（转写或整理失败后重试）"""
    retry_type: str = Field(..., description="重试类型：transcription（重新转写）/ refinement（重新整理）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "retry_type": "transcription"
            }
        }


# ===== 脚本研究相关表单 =====

class ScriptResearchFilterForm(BaseFilterForm):
    """脚本研究筛选表单"""
    status: Optional[int] = Field(None, description="研究状态")
    script_id: Optional[int] = Field(None, description="脚本ID", gt=0)


class StartResearchForm(BaseModel):
    """开始脚本研究表单
    
    用户点击"研究"按钮时，创建研究会话和研究记录。
    可选择性提供脚本的数据表现信息。
    """
    script_id: int = Field(..., description="要研究的脚本ID", gt=0)
    performance_data: Optional[dict] = Field(
        None, 
        description="脚本的数据表现（可选）",
        json_schema_extra={
            "example": {
                "views": 100000,
                "likes": 5000,
                "comments": 800,
                "shares": 200,
                "completion_rate": 0.85,
                "engagement_rate": 0.12
            }
        }
    )
    initial_thoughts: Optional[str] = Field(
        None,
        max_length=1000,
        description="用户的初步想法（可选）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "script_id": 123,
                "performance_data": {
                    "views": 100000,
                    "likes": 5000,
                    "comments": 800
                },
                "initial_thoughts": "这个脚本效果特别好，观众反馈很积极"
            }
        }


class ResearchChatForm(BaseModel):
    """研究对话表单
    
    在研究会话中，用户与AI进行交互式复盘。
    复用对话系统，但增加研究特定的上下文。
    """
    research_id: int = Field(..., description="研究记录ID", gt=0)
    content: str = Field(..., min_length=1, max_length=10000, description="用户回复内容")
    model_type: Optional[str] = Field('deepseek', description="AI模型类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "research_id": 456,
                "content": "我觉得最大的亮点是开头的那个场景，观众一下就有代入感了"
            }
        }


class UpdateResearchDataForm(BaseModel):
    """更新研究数据表单
    
    在研究过程中或结束时，更新研究记录的数据。
    通常在AI分析完成后，由后端自动调用。
    """
    performance_data: Optional[dict] = Field(None, description="数据表现")
    key_findings: Optional[list] = Field(None, description="关键成功要素")
    user_feedback: Optional[dict] = Field(None, description="用户反馈")
    ai_analysis: Optional[dict] = Field(None, description="AI分析结果")
    success_patterns: Optional[list] = Field(None, description="成功模式")
    summary: Optional[str] = Field(None, max_length=1000, description="研究总结")


class CompleteResearchForm(BaseModel):
    """完成研究表单
    
    用户确认研究完成，最终确定提炼的经验要素。
    """
    key_findings: list = Field(
        ..., 
        min_length=1,
        max_length=5,
        description="最终确认的关键成功要素（3-5个）"
    )
    summary: str = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        description="研究总结"
    )
    apply_to_profile: bool = Field(
        default=True,
        description="是否应用到个人创作档案"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "key_findings": [
                    "痛点切入式开头，用了具体职场场景",
                    "3个案例结构，节奏紧凑",
                    "使用了5个金句作为记忆点"
                ],
                "summary": "这个脚本成功的关键在于精准的痛点切入和紧凑的节奏",
                "apply_to_profile": True
            }
        }


class ArchiveResearchForm(BaseModel):
    """归档研究表单"""
    archive_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="归档原因（可选）"
    )


class ScriptMediaForm(BaseModel):
    """脚本AI生图触发表单"""
    media_type: int = Field(
        ...,
        description="素材类型：10=封面(4K·3:4), 20=素材(4K·4:3)"
    )
    custom_prompt: Optional[str] = Field(
        None,
        max_length=1000,
        description="自定义提示词（可选，留空则自动从脚本内容生成）"
    )

