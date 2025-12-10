from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session
from ...db import sm
from .fields import BaseField
from .models import Settings as Model


class _None:
    pass


class SettingsBase:
    def __init__(self):
        self._cache = {}
        self._empty = True

    def get(self, item, hook=True, load_all=True):
        field = super().__getattribute__(item)
        if isinstance(field, BaseField):
            key = item
            if load_all and self._empty:
                self._empty = False
                with sm.transaction_scope() as db:
                    q = db.query(Model)
                    for model in q:
                        self._cache[model.key] = model.value
            rv = self._cache.get(key, _None)
            if rv is _None:
                model = None
                with sm.transaction_scope() as db:
                    if self._empty:
                        model = db.query(Model).filter(Model.key == key).one_or_none()
                    if model is None:
                        rv = field.default
                    else:
                        self._cache[key] = model.value
                        rv = field.deserialize(model.value)
            else:
                rv = field.deserialize(rv)
            if hook:
                rv = getattr(self, 'get_' + item,
                             lambda x: field.after_get(item, key, x))(rv)
            return rv
        return field

    def __getattribute__(self, item):
        get = super().__getattribute__('get')
        return get if item == 'get' else get(item)

    def __setattr__(self, item, value):
        field = getattr(self.__class__, item, None)
        if isinstance(field, BaseField):
            hook = getattr(self, 'set_' + item, None)
            key = item
            if hook is not None:
                value = hook(value)
            data = field.serialize(value)
            with sm.transaction_scope() as sa:
                model = sa.query(Model).filter(Model.key == key).with_for_update().one_or_none()
                if model:
                    model.value = data
                else:
                    Model.create(sa, key=key, value=data)
            self._cache[key] = data
        else:
            self.__dict__[item] = value

