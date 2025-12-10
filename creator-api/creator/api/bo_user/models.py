"""
A user has a single role.
A role is associated with a set of permissions.
"""
from datetime import timedelta, datetime
from sqlalchemy import func
from typing import List, Optional
from sqlalchemy.ext.hybrid import hybrid_property
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
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    Query,
    Session,
    backref
)

from ...db import Base, CRUDMixin, ProfileMixin
from ..constants import BoPermission
from ..utils import mask_value


class BoRoleXPermission(CRUDMixin):
    __tablename__ = 'bo_role_x_permissions'
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('bo_roles.id'), nullable=False, index=True
    )
    permission: Mapped[str] = mapped_column(nullable=False, index=True)


class BoRole(CRUDMixin):
    __tablename__ = 'bo_roles'

    name: Mapped[str] = mapped_column(unique=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column()
    permissions: Mapped[List["BoRoleXPermission"]] = relationship(
        'BoRoleXPermission',
        cascade='all, delete-orphan',
        lazy='selectin'
    )
    disabled_at: Mapped[Optional[datetime]] = mapped_column()

    def add_perm(self, name):
        """add permission specified by the given name.

        returns None if no such permission exists; otherwise returns the perm.
        """

        # it's not a valid permission
        if not name in BoPermission.__members__:
            return None

        # this role already has this permission
        if name in [x.permission for x in self.permissions]:
            return None

        self.permissions.append(BoRoleXPermission(
            role_id=self.id,
            permission=name,
        ))

        return name

    def set_perms(self, perms):
        permissions = [BoRoleXPermission(permission=x) for x in perms]
        self.permissions = permissions

    def dump(self, with_permission=False):
        ret =  dict(
            id=self.id,
            name=self.name,
            description=self.description,
            disabled_at=self.disabled_at,
        )

        if with_permission:
            ret['permissions'] = [x.permission for x in self.permissions]

        return ret


class BoUser(CRUDMixin, ProfileMixin):
    __tablename__ = 'bo_users'

    nickname: Mapped[Optional[str]] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    mobile: Mapped[str] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('bo_roles.id'), nullable=True)
    role: Mapped[BoRole] = relationship('BoRole',
                                        foreign_keys=role_id, backref='users')

    # @hybrid_property
    # def bound_wechat(self):
    #     ret = bool(self.wechat_users)
    #     return ret

    # @bound_wechat.expression
    # def bound_wechat(cls):
    #     return cls.wechat_users.any()

    @property
    def permissions(self):
        # inactive role does not have any permissions
        if not self.role or self.role.disabled_at:
            return []
        perms = self.role.permissions or []
        return [x.permission for x in perms]

    @property
    def name(self):
        return self.nickname if self.nickname else self.username

    # 移除以下属性
    # @property
    # def bind_url(self):
    #     pass
    #     # base_url = config.get('EXTERNAL_URL')
    #     # # bind qr code expires in 5 minutes
    #     # token = create_access_token(self, expires_delta=timedelta(seconds=300))
    #     # return f'{base_url}#/bind-bo-user?token={token}&id={self.id}'

    def dump(self, with_related=True, with_bind_url=False):
        data = dict(
            id=self.id,
            active=self.active,
            username=self.username,
            nickname=self.nickname,
            mobile=self.mobile,
            # bound_wechat=self.bound_wechat,
            role=dict(
                id=self.role.id,
                name=self.role.name,
            ),
        )

        # if with_bind_url:
        #     data['bind_url'] = self.bind_url

        if with_related:
            data.update(dict(
                role=self.role.dump(),
            ))
        return data

    def option_dump(self):
        return dict(
            id=self.id,
            name=self.name,
            role=self.role.name,
            active=self.active,
        )
