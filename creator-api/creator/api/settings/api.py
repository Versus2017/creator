from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session
from ...db import sm
from .. import router as app
from ..bo_user.security import perm_accepted
from ..constants import BoPermission
from ..decorators import validates
from ..utils import get_settings
from .fields import BaseField
from .forms import ConfigForm
from .settings import Settings as Configs


@app.get('/admin/configs')
def list_configs(settings: Configs = Depends(get_settings),
                 db: Session = Depends(sm.get_db)):
    cls = Configs
    fields = [x for x in vars(cls).keys() if not x.startswith('__')]
    ret = []
    for field_key in fields:
        field = getattr(cls, field_key, None)
        if not isinstance(field, BaseField):
            continue
        ret.append(dict(
            key=field_key,
            value=getattr(settings, field_key, None),
            name=field.name,
            desc=field.desc,
            type=field.type,
        ))
    return dict(success=True, configs=ret)


@app.put('/admin/configs')
@perm_accepted(BoPermission.live_settings_manage)
def create_config(form: ConfigForm, settings: Configs = Depends(get_settings)):
    with sm.transaction_scope() as sa:
        setattr(settings, form.key, form.value)
    return dict(success=True)

