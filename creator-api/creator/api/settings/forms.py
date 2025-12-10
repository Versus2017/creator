from typing import Optional
from pydantic import BaseModel, field_validator, ValidationError

from .settings import Settings


class ConfigForm(BaseModel):
    key: str
    value: Optional[str]

    @field_validator('key')
    def validate_key(cls, v):
        if not v:
            raise ValidationError('配置项不能为空')
        if v not in Settings.__dict__:
            raise ValidationError('该项配置不合法')
        return v

    @field_validator('value')
    def validate_value(cls, v):
        if not v:
            raise ValidationError('配置值不能为空')
        return v
