import json
import inspect
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from functools import wraps

from ..db import sm
from ..app_factory import request_context_var
from ..app_factory import auth_dep

from .bo_user.models import BoUser
from .users.models import User
from creator.config import config


async def get_jwt_authorizer(Authorize: AuthJWT = Depends(auth_dep)):
    try:
        await Authorize.jwt_required()
        return Authorize
    except AuthJWTException as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_user(Authorize: AuthJWT = Depends(get_jwt_authorizer),
                   db: Session = Depends(sm.get_db)):
    claims = await Authorize.get_raw_jwt()
    user_id = claims.get('id')
    user_type = claims.get('utype')

    if not user_id or not user_type:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user_type == 'web':
        return User.get(db, user_id)
    elif user_type == 'bo':
        return BoUser.get(db, user_id)
    else:
        raise HTTPException(status_code=404, detail="User not found")


async def get_user_id(Authorize: AuthJWT = Depends(get_jwt_authorizer)):
    claims = await Authorize.get_raw_jwt()
    user_id = claims.get('id')
    user_type = claims.get('utype')

    if not user_id or not user_type:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = request_context_var.get()
        headers = request.headers
        is_from_bo = headers.get("source") == "bo"
        is_from_web = headers.get("source") == "web"
        if not is_from_bo and not is_from_web:
            raise HTTPException(status_code=403, detail="Login required")
        # 检查被装饰函数是否是异步的
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return wrapper


def user_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = request_context_var.get()
        headers = request.headers
        if headers.get("source") != "web":
            raise HTTPException(status_code=403, detail="WEB access required")
        # 检查被装饰函数是否是异步的
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return wrapper


def bo_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = request_context_var.get()
        headers = request.headers
        if headers.get("source") != "bo":
            raise HTTPException(status_code=403, detail="BO access required")
        # 检查被装饰函数是否是异步的
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper


def install():
    @AuthJWT.load_config
    def get_config():
        return config

