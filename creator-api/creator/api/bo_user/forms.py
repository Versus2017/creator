from typing import Optional
from pydantic import BaseModel, field_validator, ValidationError
from ..forms import BaseFilterForm


class LoginForm(BaseModel):
    username: str
    password: str


class TwoFAForm(BaseModel):
    code: str


class RoleListFilterForm(BaseFilterForm):
    keyword: Optional[str] = None


class RoleForm(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    permissions: list


class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str
    password_verify: str

    @field_validator('password_verify')
    def password_verify(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入密码必须一致')
        return v


class UserListFilterForm(BaseFilterForm):
    keyword: Optional[str] = None
    role_id: Optional[int] = None
    active: Optional[int] = None
    bound_wechat: Optional[int] = None


class UserForm(BaseModel):
    id: Optional[int] = None
    nickname: Optional[str] = None
    username: str
    password: str
    confirm_password: str
    mobile: str
    role_id: int
    active: Optional[bool] = None

    @field_validator('password')
    def validate_password(cls, v, values):
        confirm_password = values.get('confirm_password')
        if confirm_password and v != confirm_password:
            raise ValueError('两次输入密码必须一致')
        if not values.get('id') and not v:
            raise ValueError('密码为必填项')

    @field_validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if not values.get('id') and not v:
            raise ValueError('确认密码为必填项')


def validate_user_form(data):
    try:
        form = UserForm(**data)
        return dict(success=True, data=form.dict())
    except ValidationError as e:
        return dict(success=False, message='验证失败', errors=e.errors())
