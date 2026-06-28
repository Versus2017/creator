import copy
import sys
import os
from collections import deque
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional
from contextlib import contextmanager
from datetime import date, datetime
from creator.api.forms import BaseFilterForm

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    create_engine,
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
    sessionmaker,
    relationship,
    Query,
    Session,
    declarative_base
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from .config import config

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

Base = declarative_base()


class DatabaseSessionManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False,
                                         bind=self.engine)

    @contextmanager
    def transaction_scope(self):
        """Provide a transactional scope around a series of operations."""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            print(e, '------------ db rollback ------------')
            db.rollback()
            raise HTTPException(status_code=500,
                                detail="Internal Server Error")
        finally:
            db.close()

    def get_db(self):
        """Dependency to get DB session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# 实例化数据库会话管理器
sm = DatabaseSessionManager(config.SQLALCHEMY_DATABASE_URI)


class Rollback(Exception):
    def __init__(self, propagate=None):
        self.propagate = propagate


class CRUDMixin(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    @classmethod
    def create(cls, db: Session, **kwargs):
        instance = cls(**kwargs)
        db.add(instance)
        db.flush()
        return instance

    @classmethod
    def get(cls, db: Session, id_):
        return db.query(cls).filter(cls.id == id_).first()

    @classmethod
    def get_or_404(cls, db: Session, id_):
        instance = cls.get(db, id_)
        if not instance:
            raise HTTPException(status_code=404, detail="Item not found")
        return instance

    @classmethod
    def exists(cls, db: Session, *filters):
        return db.query(db.query(cls).filter(*filters).exists()).scalar()

    @classmethod
    def paginated_dump(cls, query=None,
                       form: BaseFilterForm = None,
                       dump_func=None,
                       extra_fields=None, **kwargs):
        page = form.page or 1
        per_page = form.per_page or 10
        if extra_fields is None:
            extra_fields = dict()
        total = query.count()
        pages = (total + per_page - 1) // per_page  # 计算总页数
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return dict(
            success=True,
            rows=[
                dump_func(row, **kwargs) if dump_func else row.dump(**kwargs)
                for row in items],
            pagination=dict(
                page=page,
                total=total,
                has_prev=page > 1,
                has_next=page < pages,
                first=1,
            ),
            **extra_fields,
        )

    def save(self, db: Session):
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def update(self, db: Session, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db: Session):
        db.delete(self)
        db.commit()


class TrackableMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=datetime.utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                           index=True)

    @declared_attr
    def created_by(cls):
        return Column(
            BigInteger(), ForeignKey('bo_users.id'), nullable=True)

    @declared_attr
    def creator(cls):
        return relationship('BoUser', foreign_keys=cls.created_by)

    @declared_attr
    def updated_by(cls):
        return Column(
            BigInteger(), ForeignKey('bo_users.id'), nullable=True)

    @declared_attr
    def updater(cls):
        return relationship('BoUser', foreign_keys=cls.updated_by)


#
# class PermissionMixin:
#     permissions = Column(MutableDict.as_mutable(JSONB),
#                             nullable=False, server_default='{}')
#
#     def get_permission(self, name):
#         from flask_principal import Permission, Denial
#         rv = Permission()
#         permission = self.permissions.get(name)
#         if permission:
#             needs, excludes = permission
#             rv = rv.union(Permission(*map(tuple, needs)))
#             rv = rv.union(Denial(*map(tuple, excludes)))
#         return rv
#
#     def set_permission(self, name, permission):
#         self.permissions[name] = (
#             list(permission.needs), list(permission.excludes))


# noinspection PyPep8Naming
# class permission_property:
#     """Makes a permission property.
#
#     Together with `PermissionMixin`, a permission property exposes the
#     operation interface of the permission with the same name as the decorated
#     method, plus the returned result of the decorated method. In action, getter
#     will union the permission loaded from database with the returned result;
#     setter will store the difference of the given permission than returned
#     result of the decorated method; deleter will simply clear database value,
#     leaving only the returned result if any.
#
#     Works similarly as a normal `property` without `PermissionMixin`.
#
#     The result of the getter is guaranteed to be a `Permission` object.
#     """
#     def __init__(self, factory):
#         self.name = factory.__name__
#         self.factory = factory
#
#     def __get__(self, instance, owner):
#         from flask_principal import Permission
#         if instance is None:
#             return self
#         rv = self.factory(instance)
#         if rv is None:
#             rv = Permission()
#         if isinstance(instance, PermissionMixin):
#             rv = rv.union(instance.get_permission(self.name))
#         return rv
#
#     def __set__(self, instance, value):
#         if isinstance(instance, PermissionMixin):
#             from flask_principal import Permission
#             if value is None:
#                 self.__delete__(instance)
#             else:
#                 instance.set_permission(
#                     self.name, value.difference(self.factory(instance)))
#         else:
#             raise AttributeError('can\'t set attribute')
#
#     def __delete__(self, instance):
#         if isinstance(instance, PermissionMixin):
#             instance.permissions.pop(self.name, None)
#         else:
#             raise AttributeError('can\'t delete attribute')

class QueryWithSoftDelete(Query):
    def __new__(cls, *args, **kwargs):
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        obj._without_deleted = kwargs.pop('_without_deleted', False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            if not obj._without_deleted:
                obj = obj.filter_by(deleted_at=None)
        return obj

    def without_deleted(self):
        # 使用 column_descriptions 获取映射类
        mapper_class = self.column_descriptions[0]['entity']
        return self.__class__(
            mapper_class,
            session=self.session,
            _without_deleted=True
        )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                           nullable=True)

    @declared_attr
    def query(cls):
        return Session.query_property(query_cls=QueryWithSoftDelete)

    @classmethod
    def get_or_404_without_deleted(cls, session, pk, pk_col='id'):
        try:
            return session.query(cls).without_deleted().filter(
                getattr(cls, pk_col) == pk).one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Item not found")

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()

    @hybrid_property
    def is_deleted(self):
        return self.deleted_at is not None

    @is_deleted.expression
    def is_deleted(cls):
        return cls.deleted_at.isnot(None)

    @is_deleted.setter
    def is_deleted(self, value):
        if value:
            self.soft_delete()
        else:
            self.deleted_at = None


class ProfileMixin:
    profile: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __init__(self, *args, **kwargs):
        # 确保在创建对象时，如果没有提供profile，则设置为空字典
        if 'profile' not in kwargs:
            kwargs['profile'] = {}
        super().__init__(*args, **kwargs)


class _None:
    pass


class _Wrapper:
    def __init__(self, parent):
        self.parent = parent
        self.method = None

    def __call__(self, method):
        self.method = method
        return self.parent

    def call(self, instance, val):
        if self.method is not None:
            val = self.method(instance, val)
        return val


# noinspection PyPep8Naming
class json_property:
    def __init__(self, default_factory):
        self.name = default_factory.__name__
        self.default_factory = default_factory
        self.expression = _Wrapper(self)
        self.after_get = _Wrapper(self)
        self.before_set = _Wrapper(self)

    def __get__(self, instance, owner):
        if instance is None:
            return self.expression.call(owner, owner.profile[self.name])
        val = instance.profile.get(self.name, _None)
        if val is _None:
            val = self.default_factory(instance)
        return self.after_get.call(instance, copy.deepcopy(val))

    def __set__(self, instance, value):
        instance.profile[self.name] = self.before_set.call(instance, value)
        # 标记 profile 字段已更改
        flag_modified(instance, 'profile')

    def __delete__(self, instance):
        instance.profile.pop(self.name, None)


# noinspection PyPep8Naming
class string_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext)


# noinspection PyPep8Naming
class datetime_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(DateTime))
        self.after_get(self.getter)
        self.before_set(self.setter)

    def getter(self, instance, val):
        if val:
            val = datetime.strptime(val, DATETIME_FORMAT)
        return val

    def setter(self, instance, val):
        if isinstance(val, datetime):
            val = val.strftime(DATETIME_FORMAT)
        return val


# noinspection PyPep8Naming
class integer_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(Integer))
        self.after_get(self.getter)
        self.before_set(self.setter)

    def getter(self, instance, val):
        if val is not None:
            val = int(val)
        return val

    def setter(self, instance, val):
        if val is not None:
            val = int(val)
        return val


# noinspection PyPep8Naming
class float_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(Float))
        self.after_get(self.getter)
        self.before_set(self.setter)

    def getter(self, instance, val):
        if val is not None:
            val = float(val)
        return val

    def setter(self, instance, val):
        if val is not None:
            val = float(val)
        return val


# noinspection PyPep8Naming
class bool_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(Boolean))
        self.after_get(lambda *x: bool(x[1]))
        self.before_set(lambda *x: bool(x[1]))


# noinspection PyPep8Naming
class object_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.after_get(lambda *x: dict(x[1] or {}))
        self.before_set(lambda *x: dict(x[1] or {}))


# noinspection PyPep8Naming
class array_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.after_get(lambda *x: list(x[1] or []))
        self.before_set(lambda *x: list(x[1] or []))


# noinspection PyPep8Naming
class price_property(integer_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(Integer))
        self.after_get(self.getter)
        self.before_set(self.setter)

    def getter(self, instance, val):
        if val is not None:
            val = int(val) / 100
        return val

    def setter(self, instance, val):
        if val is not None:
            val = round(float(val) * 100)
        return val


# noinspection PyPep8Naming
class date_property(json_property):
    def __init__(self, default_factory):
        super().__init__(default_factory)
        self.expression(lambda *x: x[1].astext.cast(Date))
        self.after_get(self.getter)
        self.before_set(self.setter)

    def getter(self, instance, val):
        if val:
            val = datetime.strptime(val, DATE_FORMAT)
        return val

    def setter(self, instance, val):
        if isinstance(val, date):
            val = val.strftime(DATE_FORMAT)
        return val


# noinspection PyPep8Naming
class cst_datetime_property(datetime_property):
    def getter(self, instance, val):
        if val:
            from .api.utils import user_timezone
            val = datetime.strptime(val, DATETIME_FORMAT)
            val = val.replace(tzinfo=user_timezone)
        return val


# class TaskError(CRUDMixin, Model):
#     __tablename__ = 'task_errors'
#
#     task = sa.Column(sa.Unicode())
#     traceback = sa.Column(sa.Unicode())
#     args = sa.Column(JSONB())
#     created_at = sa.Column(sa.DateTime(), nullable=False,
#                            default=datetime.utcnow)


# noinspection PyUnresolvedReferences
def install():
    from .api.bo_user import models
    from .api.settings import models
    from .api.users import models
    from .api.media import models
    from .api.conversations import models  # TODO: 修复models定义后再启用
