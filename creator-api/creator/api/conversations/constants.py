from ..utils import Enum, IntEnum
from ..fixtures import register_enum


class ConversationStatus(IntEnum):
    """会话状态"""
    IN_PROGRESS = 10
    COMPLETED = 20
    ARCHIVED = 30


ConversationStatus.IN_PROGRESS.label = '进行中'
ConversationStatus.COMPLETED.label = '已完成'
ConversationStatus.ARCHIVED.label = '已归档'

register_enum(ConversationStatus)


class ConversationType(IntEnum):
    """对话类型"""
    CREATION = 10
    RESEARCH = 20


ConversationType.CREATION.label = '创作对话'
ConversationType.RESEARCH.label = '研究对话'

register_enum(ConversationType)


class MessageRole(Enum):
    """消息角色"""
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


MessageRole.USER.label = '用户'
MessageRole.ASSISTANT.label = 'AI助手'
MessageRole.SYSTEM.label = '系统'

register_enum(MessageRole)


class ScriptStatus(IntEnum):
    """脚本状态"""
    DRAFT = 10
    COMPLETED = 20
    PUBLISHED = 30


ScriptStatus.DRAFT.label = '草稿'
ScriptStatus.COMPLETED.label = '已完成'
ScriptStatus.PUBLISHED.label = '已发布'

register_enum(ScriptStatus)


class ScriptFormatType(Enum):
    """脚本格式类型"""
    VLOG = 'vlog'
    TUTORIAL = 'tutorial'
    STORY = 'story'
    PROMOTION = 'promotion'


ScriptFormatType.VLOG.label = 'Vlog'
ScriptFormatType.TUTORIAL.label = '教程'
ScriptFormatType.STORY.label = '故事'
ScriptFormatType.PROMOTION.label = '带货'

register_enum(ScriptFormatType)


class TranscriptionStatus(IntEnum):
    """语音转写状态"""
    PENDING = 10
    PROCESSING = 20
    COMPLETED = 30
    FAILED = 40


TranscriptionStatus.PENDING.label = '等待转写'
TranscriptionStatus.PROCESSING.label = '转写中'
TranscriptionStatus.COMPLETED.label = '转写完成'
TranscriptionStatus.FAILED.label = '转写失败'

register_enum(TranscriptionStatus)


class RefinementStatus(IntEnum):
    """内容整理状态"""
    PENDING = 10
    PROCESSING = 20
    COMPLETED = 30
    FAILED = 40


RefinementStatus.PENDING.label = '等待整理'
RefinementStatus.PROCESSING.label = '整理中'
RefinementStatus.COMPLETED.label = '整理完成'
RefinementStatus.FAILED.label = '整理失败'

register_enum(RefinementStatus)


class ResearchStatus(IntEnum):
    """脚本研究状态"""
    IN_PROGRESS = 10
    COMPLETED = 20
    ARCHIVED = 30


ResearchStatus.IN_PROGRESS.label = '研究中'
ResearchStatus.COMPLETED.label = '研究完成'
ResearchStatus.ARCHIVED.label = '已归档'

register_enum(ResearchStatus)

