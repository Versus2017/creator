from sqlalchemy import (
    create_engine,
    Unicode,
    Text,
    Column,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    Date
)
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    Query,
    Session,
    backref
)
from ..bo_user.models import BoUser
from ..constants import BoPermission
from ...db import (
    CRUDMixin,
    ProfileMixin,
    sm,
    string_property,
    array_property,
)
from ..media.models import MediaModel
from ..bo_user.verify_code import code_verification


logger = logging.getLogger(__name__)


class User(CRUDMixin, ProfileMixin):
    __tablename__ = 'users'

    openid: Mapped[str] = mapped_column(Unicode, unique=True, nullable=True)
    mobile: Mapped[str] = mapped_column(Unicode, unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(Unicode, nullable=True)
    # 用户头像
    avatar_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('media.id'), index=True, nullable=True
    )
    avatar: Mapped["MediaModel"] = relationship(
        'MediaModel', foreign_keys=[avatar_id]
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                           index=True)
    disabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                            index=True)

    @string_property
    def source(self):
        pass

    @string_property
    def introduction(self):
        """用户自我介绍"""
        pass

    @string_property
    def ai_summary(self):
        """AI分析总结的简介"""
        pass

    @array_property
    def tags(self):
        """AI提取的用户标签"""
        pass

    # 发送登录验证码短信
    @classmethod
    def send_login_verification_code(cls, mobile):
        from creator.api.notifications.tasks import send_sms_by_tpl
        from creator.api.notifications.templates import SMS_TEMPLATE
        from creator.config import config
        if not mobile:
            logger.info(
                'Mobile is None, can not send message',
            )
            return
        # 使用手机号作为 key， 存到 redis 里
        code = code_verification.get_or_create(mobile)
        if not config.MESSAGE_SEND_ENABLED:
            logger.info('*' * 40)
            logger.info(
                'Stop sending sms verify code %s to %s',
                code, mobile
            )
            logger.info('*' * 40)
            return
        # todo: 发送短信验证码
        send_sms_by_tpl(
            SMS_TEMPLATE.LOGIN_VERIFICATION,
            mobile,
            code=code,
            ttl_min=int(code_verification.ttl / 60)
        )

    def auth_dump(self):
        return dict(
            id=self.id,
            openid=self.openid,
            mobile=self.mobile,
            nickname=self.nickname,
            avatar=self.avatar.url if self.avatar else None,
        )

    def dump(self):
        return dict(
            id=self.id,
            openid=self.openid,
            mobile=self.mobile,
            nickname=self.nickname,
            avatar=self.avatar.url if self.avatar else None,
            introduction=self.introduction,
            ai_summary=self.ai_summary,
            tags=self.tags,
            created_at=self.created_at,
            updated_at=self.updated_at,
            disabled_at=self.disabled_at,
        )



