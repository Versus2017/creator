import logging
import json
from fastapi import Depends, Request, Response, HTTPException
from async_fastapi_jwt_auth import AuthJWT
from fastapi.responses import RedirectResponse
from jinja2 import Template
from sqlalchemy.orm import Session
from ...app_factory import auth_dep

from ...db import sm
from .. import router as app
from ..decorators import validates, validates_args
from ..jwt import get_user, user_required
from ..wechat import wechat
from .forms import BaseFilterForm, UserSendCodeForm, UserLoginForm, UserUpdateForm
from .models import User
from .tasks import analyze_user_profile
from ...config import config
from ..bo_user.verify_code import code_verification

logger = logging.getLogger(__name__)


@app.get('/web/users/me')
@user_required
async def web_user_me(user: User = Depends(get_user)):
    # 每次获取用户信息时返回最新数据
    # 注意：User对象在Depends中获取，如果后续有更新操作，需要确保返回的是最新状态
    return dict(success=True, user=user.dump())


@app.post('/web/users/me')
@user_required
async def update_user_profile(
    form: UserUpdateForm,
    current_user: User = Depends(get_user)
):
    """更新用户个人信息"""
    
    # 检查是否需要调用AI分析（只有当introduction更新且不为空时）
    need_ai_analysis = False
    if form.introduction is not None and form.introduction != current_user.introduction:
        need_ai_analysis = True
        
    with sm.transaction_scope() as sa:
        user = User.get_or_404(sa, current_user.id)
        
        # 更新基础字段
        if form.nickname is not None:
            user.nickname = form.nickname
        
        if form.avatar_id is not None:
            # 验证头像是否存在（可选，视MediaModel设计而定）
            user.avatar_id = form.avatar_id
            
        # 更新简介
        if form.introduction is not None:
            user.introduction = form.introduction
        
        # 保存并获取更新后的数据
        result = user.dump()

    # 触发AI分析任务（异步）
    if need_ai_analysis and form.introduction:
        analyze_user_profile.schedule((current_user.id,), delay=0)
        logger.info(f"Scheduled AI analysis for user {current_user.id}")

    return dict(success=True, data=result)


@app.post('/web/send_code')
@user_required
async def send_validation_code(form: UserSendCodeForm,
                               db: Session = Depends(sm.get_db)):
    mobile = form.mobile
    user = db.query(User).filter_by(mobile=mobile).first()
    if user and user.disabled_at:
        raise HTTPException(status_code=400, detail='用户已禁用')
    User.send_login_verification_code(mobile)
    return dict(success=True)


@app.post('/web/login')
@user_required
async def app_login(form: UserLoginForm,
                    db: Session = Depends(sm.get_db),
                    authorize: AuthJWT = Depends(auth_dep)):
    mobile = form.mobile
    code = form.code
    if not code_verification.is_code_valid(mobile):
        return dict(success=False, code=400, message='验证码已过期，请重新获取')
    if not code_verification.verify(mobile, code, True):
        raise HTTPException(status_code=400, detail='验证码错误')
    user = db.query(User).filter_by(mobile=mobile).first()
    user_info = None
    user_id = None
    if not user:
        with sm.transaction_scope() as sa:
            user = User.create(sa, profile={}, mobile=mobile)
            user.source = 'pc'
            user_id = user.id
            user_info = user.auth_dump()
    else:
        user_id = user.id
        user_info = user.auth_dump()
        # ✅ 在 transaction_scope 内完成所有属性访问
        with sm.transaction_scope() as sa:
            user = User.get_or_404(sa, user_id) # 重新获取对象
            
            # 检查用户是否被禁用（必须在 session 关闭前）
            if user.disabled_at:
                raise HTTPException(status_code=400, detail='用户已禁用')
            
            user.source = 'pc'
    user_info['utype'] = 'web'
    # 返回token
    token = await authorize.create_access_token(
        user_id,
        user_claims=user_info)
    await authorize.set_access_cookies(
        token, max_age=config.AUTHJWT_ACCESS_TOKEN_EXPIRES)

    return dict(success=True, data={'token': token})


@app.post('/web/logout')
@user_required
async def web_logout(authorize: AuthJWT = Depends(auth_dep)):
    resp = dict(success=True)
    await authorize.jwt_required()
    await authorize.unset_jwt_cookies()
    return resp
