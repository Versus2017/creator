from typing import Optional
from fastapi import Depends
from pydantic import BaseModel, Field, field_validator, ValidationError
from sqlalchemy.orm import Session
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from ...app_factory import auth_dep
from ..bo_user.models import BoUser
from ..utils import config
from ...db import sm
from ..forms import BaseFilterForm


class UserFilterForm(BaseFilterForm):
    keyword: Optional[str] = None


class UserSendCodeForm(BaseModel):
    mobile: str = Field(..., pattern="^1[3-9]\d{9}$", description="手机号码")

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v):
        if not v:
            raise ValueError('手机号为必填项')
        return v


class UserLoginForm(BaseModel):
    mobile: str = Field(..., pattern="^1[3-9]\d{9}$", description="手机号码")
    code: str = Field(..., min_length=6, max_length=6, pattern="^\d{6}$", description="验证码")


class UserUpdateForm(BaseModel):
    """用户更新表单"""
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_id: Optional[int] = Field(None, gt=0)
    introduction: Optional[str] = Field(
        None, 
        max_length=500, 
        description="用户自我介绍，最多500字"
    )
