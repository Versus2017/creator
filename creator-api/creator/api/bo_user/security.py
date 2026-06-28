from functools import partial, wraps
from ..constants import BoPermission
from .models import BoUser
from creator.api.jwt import bo_required, get_user
from fastapi import FastAPI, Depends, HTTPException, status, Request
from typing import List
from async_fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
import bcrypt
from ...db import sm
from ...app_factory import request_context_var


# 权限检查函数
def has_any_perm(user_perms: List[BoPermission], perms: List[BoPermission]) -> bool:
    return any(perm.value in user_perms for perm in perms)


# 权限装饰器
def perm_accepted(*perms: BoPermission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            permissions: List[BoPermission] = await get_bo_user()
            if not permissions:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
            if not has_any_perm(permissions, perms):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
            return func(*args, **kwargs)
        return wrapper
    return decorator


async def get_bo_user():
    db_generator = sm.get_db()  # 获取生成器对象
    db = next(db_generator)  # 获取实际的数据库会话对象
    try:
        request: Request = request_context_var.get()
        headers = request.headers
        if headers.get("source") != "bo":
            print('source not bo')
            return None
        authorize = AuthJWT(request)
        await authorize.jwt_required()
        claims = await authorize.get_raw_jwt()
        user_id = claims.get('id')
        user_type = claims.get('utype')
        if user_type != 'bo':
            print('user type not bo')
            return None
        user = BoUser.get(db, user_id)
        if not user:
            print('user not found')
            return None
        return user.permissions
    finally:
        db.close()  # 确保在完成后关闭数据库会话



# 生成密码哈希
def generate_hash_password(password: str) -> str:
    # 使用 bcrypt.gensalt() 生成一个随机盐值
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


# 验证密码
def verify_hash_password(plain_password: str, hashed_password: str) -> bool:
    # 验证输入的密码与存储的哈希密码是否匹配
    return bcrypt.checkpw(plain_password.encode('utf-8'),
                          hashed_password.encode('utf-8'))
