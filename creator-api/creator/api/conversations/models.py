from sqlalchemy import (
    Unicode,
    Text,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
)
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from ...db import (
    CRUDMixin,
    ProfileMixin,
    TrackableMixin,
    string_property,
    integer_property,
    object_property,
    array_property,
)
from .constants import (
    ConversationStatus,
    ConversationType,
    MessageRole,
    ScriptStatus,
    ScriptFormatType,
    TranscriptionStatus,
    RefinementStatus,
    ResearchStatus,
)


logger = logging.getLogger(__name__)


class Conversation(CRUDMixin, ProfileMixin):
    """AI对话会话"""
    __tablename__ = 'conversations'

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id'), index=True, comment='用户ID'
    )
    title: Mapped[str] = mapped_column(
        Unicode(200), comment='会话标题'
    )
    topic: Mapped[str] = mapped_column(
        Unicode(500), comment='视频主题'
    )
    conversation_type: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, index=True, comment='对话类型：10=创作对话, 20=研究对话'
    )
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=ConversationStatus.IN_PROGRESS.value,
        index=True, comment='会话状态'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    @object_property
    def context_summary(self):
        """对话上下文摘要"""
        pass

    @integer_property
    def message_count(self):
        """消息数量"""
        pass

    @integer_property
    def total_tokens(self):
        """累计消耗token数"""
        pass

    def dump(self):
        from .constants import ConversationType
        return dict(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            topic=self.topic,
            conversation_type=ConversationType.init(self.conversation_type).dump(),
            status=ConversationStatus.init(self.status).dump(),
            context_summary=self.context_summary,
            message_count=self.message_count,
            total_tokens=self.total_tokens,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )


class Message(CRUDMixin, ProfileMixin):
    """对话消息"""
    __tablename__ = 'messages'

    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('conversations.id'), index=True, comment='会话ID'
    )
    role: Mapped[str] = mapped_column(
        Unicode(20), comment='消息角色'
    )
    content: Mapped[str] = mapped_column(
        Text, comment='消息内容'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    # ===== 原有字段 =====
    @string_property
    def audio_url(self):
        """语音文件URL（已废弃，使用audio_media_id）"""
        pass

    @integer_property
    def audio_duration(self):
        """语音时长（秒）"""
        pass

    @integer_property
    def token_count(self):
        """token消耗数"""
        pass

    @object_property
    def api_metadata(self):
        """API调用元数据"""
        pass

    # ===== 语音识别相关字段 =====
    @integer_property
    def audio_media_id(self):
        """音频文件Media ID（关联media表）"""
        pass

    @integer_property
    def transcription_status(self):
        """转写状态（TranscriptionStatus枚举值）"""
        pass

    @string_property
    def raw_transcription(self):
        """原始转写文本（口语化、未整理）"""
        pass

    @object_property
    def transcription_segments(self):
        """转写分段信息（仅长音频，用于前端展示）
        {
            "segment_count": 3,
            "total_duration": 600,
            "segments": [
                {
                    "index": 0,
                    "start_time": 0.0,
                    "end_time": 180.5,
                    "text": "这段的文本...",
                    "duration": 180.5,
                    "word_count": 256
                }
            ]
        }
        """
        pass

    @string_property
    def transcription_error(self):
        """转写错误信息（如果失败）"""
        pass

    @integer_property
    def refinement_status(self):
        """整理状态（RefinementStatus枚举值）"""
        pass

    @object_property
    def refinement_result(self):
        """AI整理结果
        {
            "user_intent": "用户核心意图",
            "thinking_process": "思考演进过程",
            "key_points": ["要点1", "要点2"],
            "structure_suggestion": "结构建议",
            "final_text": "整理后的完整文本",
            "unclear_parts": ["需要澄清的部分"]
        }
        """
        pass

    @string_property
    def refined_content(self):
        """整理后的文本（快速访问）"""
        pass

    @string_property
    def refinement_error(self):
        """整理错误信息（如果失败）"""
        pass

    @integer_property
    def user_confirmed(self):
        """用户是否确认（0=未确认, 1=已确认）"""
        pass

    def dump(self):
        return dict(
            id=self.id,
            conversation_id=self.conversation_id,
            role=self.role,
            content=self.content,
            # 原有字段
            audio_url=self.audio_url,
            audio_duration=self.audio_duration,
            token_count=self.token_count,
            api_metadata=self.api_metadata,
            # 语音识别字段
            audio_media_id=self.audio_media_id,
            transcription_status=TranscriptionStatus.init(self.transcription_status).dump() if self.transcription_status else None,
            raw_transcription=self.raw_transcription,
            transcription_segments=self.transcription_segments,
            transcription_error=self.transcription_error,
            refinement_status=RefinementStatus.init(self.refinement_status).dump() if self.refinement_status else None,
            refinement_result=self.refinement_result,
            refined_content=self.refined_content,
            refinement_error=self.refinement_error,
            user_confirmed=bool(self.user_confirmed) if self.user_confirmed is not None else False,
            # 时间戳
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )


class Script(CRUDMixin, ProfileMixin):
    """视频脚本"""
    __tablename__ = 'scripts'

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id'), index=True, comment='用户ID'
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('conversations.id'), nullable=True, index=True, comment='关联的会话ID'
    )
    title: Mapped[str] = mapped_column(
        Unicode(200), comment='脚本标题'
    )
    content: Mapped[str] = mapped_column(
        Text, comment='脚本内容'
    )
    format_type: Mapped[str] = mapped_column(
        Unicode(50), default=ScriptFormatType.VLOG.value, comment='格式类型'
    )
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=ScriptStatus.DRAFT.value,
        index=True, comment='脚本状态'
    )
    quality_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment='质量评分'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    @string_property
    def subtitle(self):
        """脚本副标题"""
        pass

    @object_property
    def structure(self):
        """脚本结构化数据"""
        pass

    @object_property
    def quality_analysis(self):
        """质量分析结果"""
        pass

    @string_property
    def estimated_duration(self):
        """预估时长"""
        pass

    @integer_property
    def word_count(self):
        """字数统计"""
        pass

    def dump(self):
        return dict(
            id=self.id,
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            title=self.title,
            subtitle=self.subtitle,
            content=self.content,
            format_type=self.format_type,
            status=ScriptStatus.init(self.status).dump(),
            quality_score=self.quality_score,
            structure=self.structure,
            quality_analysis=self.quality_analysis,
            estimated_duration=self.estimated_duration,
            word_count=self.word_count,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )


class UserStyleProfile(CRUDMixin, ProfileMixin):
    """用户创作风格档案"""
    __tablename__ = 'user_style_profiles'

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id'), unique=True, index=True, comment='用户ID'
    )
    is_analyzed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='是否已分析'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    @object_property
    def style_dna(self):
        """风格DNA"""
        pass

    @array_property
    def reference_script_ids(self):
        """参考脚本ID列表"""
        pass

    @integer_property
    def analyzed_script_count(self):
        """已分析的脚本数量"""
        pass

    @string_property
    def last_analysis_at(self):
        """最后分析时间"""
        pass

    def dump(self):
        return dict(
            id=self.id,
            user_id=self.user_id,
            is_analyzed=self.is_analyzed,
            style_dna=self.style_dna,
            reference_script_ids=self.reference_script_ids,
            analyzed_script_count=self.analyzed_script_count,
            last_analysis_at=self.last_analysis_at,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )


class ScriptResearch(CRUDMixin, ProfileMixin):
    """脚本研究记录
    
    用于存储用户对成功脚本的深入研究和分析记录。
    通过交互式对话，AI引导用户反思成功经验，并提炼可复用的创作模式。
    """
    __tablename__ = 'script_researches'

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id'), index=True, comment='用户ID'
    )
    script_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('scripts.id'), index=True, comment='研究的脚本ID'
    )
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('conversations.id'), index=True, comment='研究对话的会话ID'
    )
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, index=True, comment='研究状态'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)

    # ===== 扩展字段（存储在 profile JSONB 中） =====
    
    @object_property
    def performance_data(self):
        """脚本的数据表现
        {
            "views": 100000,           # 播放量
            "likes": 5000,             # 点赞数
            "comments": 800,           # 评论数
            "shares": 200,             # 分享数
            "completion_rate": 0.85,   # 完播率
            "engagement_rate": 0.12    # 互动率
        }
        """
        pass
    
    @array_property
    def key_findings(self):
        """提炼的关键成功要素（3-5个）
        [
            "痛点切入式开头，用了具体职场场景",
            "3个案例结构，节奏紧凑",
            "使用了5个金句作为记忆点",
            ...
        ]
        """
        pass
    
    @object_property
    def user_feedback(self):
        """用户的主观反馈和观察
        {
            "highlights": "最满意的是第二个案例，观众反馈特别好",
            "audience_reaction": "评论区很多人说有共鸣，还有人分享自己的经历",
            "creation_context": "当时看到一个热点话题，结合了我的经验写的",
            "special_factors": ["蹭了热点", "配合了视觉冲击力的画面"]
        }
        """
        pass
    
    @object_property
    def ai_analysis(self):
        """AI的深度分析
        {
            "content_analysis": {
                "theme": "职场沟通",
                "angle": "痛点切入+解决方案",
                "information_density": "high"
            },
            "structure_analysis": {
                "opening_style": "场景式+痛点",
                "body_structure": "3个并列案例",
                "closing_style": "金句升华"
            },
            "language_style": {
                "tone": "犀利、直接",
                "sentence_pattern": "短句为主",
                "memorable_phrases_count": 5
            },
            "audience_positioning": {
                "target_group": "25-35岁职场人",
                "pain_points": ["职场沟通障碍", "晋升困境"]
            }
        }
        """
        pass
    
    @array_property
    def success_patterns(self):
        """识别出的成功模式（可复用）
        [
            {
                "pattern_type": "opening",
                "pattern_name": "痛点场景式开头",
                "description": "用具体的职场场景+痛点，快速抓住目标观众",
                "confidence": 0.9
            },
            {
                "pattern_type": "structure",
                "pattern_name": "3段式案例结构",
                "description": "3个并列案例，每个案例一个核心观点",
                "confidence": 0.85
            }
        ]
        """
        pass
    
    @string_property
    def summary(self):
        """研究总结（简短版本，用于快速展示）"""
        pass
    
    @integer_property
    def research_duration(self):
        """研究对话时长（秒）"""
        pass

    def dump(self):
        from .constants import ResearchStatus
        return dict(
            id=self.id,
            user_id=self.user_id,
            script_id=self.script_id,
            conversation_id=self.conversation_id,
            status=ResearchStatus.init(self.status).dump(),
            performance_data=self.performance_data,
            key_findings=self.key_findings,
            user_feedback=self.user_feedback,
            ai_analysis=self.ai_analysis,
            success_patterns=self.success_patterns,
            summary=self.summary,
            research_duration=self.research_duration,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )
