import json
import re
import logging

from fastapi import Depends, HTTPException, Request
from datetime import datetime
from sqlalchemy.orm import Session
from async_fastapi_jwt_auth import AuthJWT
from sqlalchemy import or_
from ...app_factory import auth_dep
from ...db import sm
from ..jwt import bo_required, get_user
from .. import router as app
from ..constants import BoPermissionGroup, BoPermission
from ..utils import settings
from .forms import (
    LoginForm,
    TwoFAForm,
    RoleForm,
    RoleListFilterForm,
    UserForm,
    UserListFilterForm,
    UpdatePasswordForm,
)
from .models import BoRole, BoUser
from .verify_code import code_verification as verify_code
from .security import (
    verify_hash_password,
    generate_hash_password,
    has_any_perm,
    perm_accepted
)
from ...config import config


logger = logging.getLogger(__name__)

MOBILE_RE = re.compile(r'^1[0-9]{10}$')

"""
Login Flow

There are 2 modes: simple and 2FA. Simple is for local testing and development

Simple:
1. client: user goes to login page. client sends username and password
2. server: checks credentials. If ok, return token.

2FA enabled:
1. client: user goes to login page. client sends username and password
2. server: checks credentials. If ok, send user a verification code via sms
   and return client a 2fa token with a short expiracy. This token can only
   access the verify_code endpoint.
3. client: redirect user to sms verification page. user enters code and send
   code to verify_code with 2fa_token
4. server: checks code. If passed, return token.
"""


def send_verification_code(user):
    # from ..notifications.tasks import send_sms_by_tpl
    # from ..notifications.templates import (
    #     TEMPLATE_NAMES,
    #     SMS_TYPE,
    # )
    # code = verify_code.get_or_create(user.id)
    # if config.DEBUG:
    #     logger.info(
    #         'sending sms verify code %s to %s',
    #         code, user.mobile
    #     )
    # send_sms_by_tpl(
    #     SMS_TYPE.PIN_CODE,
    #     TEMPLATE_NAMES.SMS_VERIFICATION,
    #     user.mobile,
    #     code=code,
    #     ttl_min=int(verify_code.ttl / 60)
    # )
    # TODO: send sms
    pass


@app.post('/admin/login')
async def login(form: LoginForm,
                db: Session = Depends(sm.get_db),
                authorize: AuthJWT = Depends(auth_dep)):
    user = db.query(BoUser).filter(BoUser.username == form.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_hash_password(form.password, user.password):
        raise HTTPException(status_code=400, detail="密码不正确")
    if not user.active:
        raise HTTPException(status_code=400, detail="用户未激活")

    # this is adapted from flask_security.views.login
    # we make its response format consistent to ours
    two_fa_enable = settings.enable_two_fa_login
    data = dict(success=True)
    user_info = user.dump()
    user_info['utype'] = 'bo'
    if two_fa_enable:
        access_token = await authorize.create_access_token(
            user.id, expires_time=config.BO_AUTH_2FA_EXPIRES, user_claims=user_info)
        # mask user mobile
        mobile = user.mobile
        data['2fa_to'] = '*' * (len(mobile) - 4) + mobile[-4:]
        # send verification code
        send_verification_code(form.user)
        resp = dict(**data)
        await authorize.set_access_cookies(access_token,
                                     max_age=config.BO_AUTH_2FA_EXPIRES)
    else:
        access_token = await authorize.create_access_token(user.id, user_claims=user_info)
        resp = dict(**data)
        await authorize.set_access_cookies(
                access_token,
                max_age=config.AUTHJWT_ACCESS_TOKEN_EXPIRES)
    return resp


@app.post('/admin/logout')
async def logout(authorize: AuthJWT = Depends(auth_dep)):
    resp = dict(success=True)
    await authorize.jwt_required()
    await authorize.unset_jwt_cookies()
    return resp


@app.post('/admin/2fa/verify')
@bo_required
async def verify_2fa(form: TwoFAForm, authorize: AuthJWT = Depends(auth_dep),
               user: BoUser = Depends(get_user)):
    code = form.code
    if not verify_code.verify(user.id, code, remove_if_match=True):
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    token = await authorize.create_access_token(user.id, user_claims=user.dump())
    await authorize.set_access_cookies(
        token, max_age=config.AUTHJWT_ACCESS_TOKEN_EXPIRES)
    return dict(success=True)


@app.get('/admin/users/me')
@bo_required
def get_user_me(user: BoUser = Depends(get_user)):
    data = user.dump(with_related=False)
    data['permissions'] = user.permissions
    return dict(
        success=True,
        user=data,
    )


@app.get('/admin/users')
@perm_accepted(BoPermission.bo_users_view, BoPermission.bo_users_manage)
def list_users(form: UserListFilterForm = Depends(),
               db: Session = Depends(sm.get_db),
               user: BoUser = Depends(get_user)):
    q = db.query(BoUser)
    if form.keyword:
        kw = form.keyword
        q = q.filter(or_(
            BoUser.username.ilike(f'%{kw}%'),
            BoUser.mobile.ilike(f'%{kw}%'),
            BoUser.nickname.ilike(f'%{kw}%'),
        ))

    if form.role_id:
        q = q.filter(BoUser.role_id == form.role_iddata)
    if form.active is not None:
        active = form.active != 0
        q = q.filter(BoUser.active == active)
    # if form.bound_wechat is not None:
    #     bound = form.bound_wechat != 0
    #     q = q.filter(BoUser.bound_wechat == bound)
    with_bind_url = has_any_perm(user.permissions, [BoPermission.bo_users_wechat_bind_manage])
    return BoUser.paginated_dump(
        query=q.order_by(BoUser.id), with_bind_url=with_bind_url, form=form)


@app.get('/admin/users/options')
@perm_accepted(BoPermission.bo_users_view)
def list_user_options(db: Session = Depends(sm.get_db)):
    q = db.query(BoUser).filter()
    return dict(
        success=True,
        rows=[u.option_dump() for u in q.order_by(BoUser.id)],
    )


@app.get('/admin/users/<int:user_id>')
@perm_accepted(BoPermission.bo_users_view)
def get_user(user_id, db: Session = Depends(sm.get_db)):
    user = BoUser.get_or_404(db, user_id)
    return dict(
        success=True,
        user=user.dump()
    )


@app.get('/admin/users/<int:user_id>/bind_wechat_url')
@perm_accepted(BoPermission.bo_users_wechat_bind_manage)
def get_bind_wechat_url(user_id, db: Session = Depends(sm.get_db)):
    user = BoUser.get_or_404(db, user_id)
    return dict(success=True, qr_url=user.bind_url)


# 移除以下接口
# @app.delete('/admin/users/<int:user_id>/wechat_user')
# @perm_accepted(BoPermission.bo_users_wechat_bind_manage)
# def unbind_wechat_user(user_id, db: Session = Depends(sm.get_db)):
#     user = BoUser.get_or_404(db, user_id)
#     if user.wechat_users:
#         with sm.transaction_scope():
#             user.wechat_users = []
#     return dict(success=True)


@app.post('/admin/users')
@perm_accepted(BoPermission.bo_users_manage)
def create_user(form: UserForm = Depends(), db: Session = Depends(sm.get_db)):
    role_id = form.role_id
    role = BoRole.exists(db, role_id)
    if not role:
        raise HTTPException(status_code=400, detail="角色不存在")
    username = form.username
    if BoUser.exists(db, BoUser.username == username):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    with sm.transaction_scope() as ts:
        user = BoUser.create(ts, username=form.username, password=form.password)
        user.nickname = form.nickname
        user.mobile = form.mobile
        user.role_id = role_id
        user.active = form.active
        user.profile = {}
        user_info = user.dump()
    return dict(
        success=True,
        user=user_info
    )


@app.put('/admin/users/<int:user_id>')
@perm_accepted(BoPermission.bo_users_manage)
def edit_user(user_id, form: UserForm = Depends(), db: Session = Depends(sm.get_db)):
    user = BoUser.get_or_404(db, user_id)
    role_id = form.role_id
    role = BoRole.exists(db, role_id)
    if not role:
        raise HTTPException(status_code=400, detail="角色不存在")
    username = form.username
    if BoUser.exists(db, BoUser.username == username):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    with sm.transaction_scope() as ts:
        if form.username:
            user.username = form.username
        if form.password:
            user.password = generate_hash_password(form.password)
        user.nickname = form.nickname
        user.mobile = form.mobile
        user.role_id = role_id
        user.active = form.active
        user_info = user.dump()

    return dict(
        success=True,
        user=user_info
    )


@app.put('/admin/users/update_password')
@perm_accepted(BoPermission.bo_users_manage)
def update_user_info(form: UpdatePasswordForm=Depends(), user: BoUser = Depends(get_user)):
    if not verify_hash_password(form.password, user.password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    with sm.transaction_scope():
        user.password = generate_hash_password(form.new_password)
    return dict(success=True)


@app.post('/admin/users/<int:users_id>/<string:mode>')
@perm_accepted(BoPermission.bo_users_manage)
def switch_user_mode(users_id, mode, db: Session = Depends(sm.get_db)):
    user = BoUser.get_or_404(db, users_id)
    active = mode != 'disable'
    if active and user.role and user.role.disabled_at:
        raise HTTPException(
            status_code=400,
            detail=f'该用户所属角色{user.role.name}已被禁用，如果要启用该用户，'
                   f'请先启用该用户所属角色') # noqa
    with sm.transaction_scope():
        user.active = active
    return dict(success=True)


@app.post('/admin/users/upload')
@perm_accepted(BoPermission.bo_users_manage)
def upload_users(request: Request, db: Session = Depends(sm.get_db)):
    valid = {}
    invalid = []
    default_pwd = 'dpai4u'

    from .forms import validate_user_form
    for row in request.json.get('data', []):
        nickname = row.get('nickname', '').strip()
        role_name = row.get('role_id', '').strip()
        username = row.get('username', '').strip()
        mobile = row.get('mobile', '').strip()

        data = dict(
            nickname=nickname,
            username=username,
            mobile=mobile,
            gems_id='',
            active=True,
        )
        if role_name:
            role = db.query(BoRole).filter(BoRole.name == role_name).first()
            if role:
                data['role_id'] = role.id
        bo_user = None
        if username:
            bo_user = db.query(BoUser).filter(BoUser.username == username).first()
        if not bo_user:
            data['password'] = default_pwd
            data['confirm_password'] = default_pwd
        else:
            data['id'] = bo_user.id

        result = validate_user_form(data)
        if not result['success']:
            invalid.append(dict(
                nickname=nickname,
                role_id=role_name,
                username=username,
                mobile=mobile,
                errors=result.errors,
            ))
            continue

        valid[username] = result

    with sm.transaction_scope() as ts:
        for username, result in valid.items():
            data = result['data']
            if 'id' in data:
                user = BoUser.get_or_404(ts, data['id'])
                data.pop('id')
                for k, v in data.items():
                    setattr(user, k, v)
            else:
                user = BoUser.create(ts, **data)
    return dict(
        success=True,
        valid_count=len(valid),
        invalid=invalid,
    )


@app.get('/admin/roles')
@perm_accepted(BoPermission.bo_roles_view, BoPermission.bo_roles_manage)
def list_roles(form: RoleListFilterForm = Depends(),
               db: Session = Depends(sm.get_db)):
    q = db.query(BoRole)
    if form.keyword:
        kw = form.keyword
        q = q.filter(BoRole.name.ilike(f'%{kw}%'))
    # TODO: page and page no
    return BoRole.paginated_dump(q.order_by(BoRole.id), form)


@app.get('/admin/roles/options')
@perm_accepted(BoPermission.bo_users_manage)
def list_roles_options(db: Session = Depends(sm.get_db)):
    q = db.query(BoRole).filter(
        BoRole.disabled_at.is_(None)
    )
    return dict(
        success=True,
        rows=[d.dump() for d in q.order_by(BoRole.name)],
    )


@app.get('/admin/roles/<int:role_id>')
@perm_accepted(BoPermission.bo_roles_manage)
def get_role(role_id, db: Session = Depends(sm.get_db)):
    role = BoRole.get_or_404(db, role_id)
    role_info = role.dump(with_permission=True)
    return dict(
        success=True,
        role=role_info,
    )


@app.post('/admin/roles')
@perm_accepted(BoPermission.bo_roles_manage)
def create_role(form: RoleForm = Depends()):
    with sm.transaction_scope() as ts:
        role = BoRole.create(ts, name=form.name, description=form.description)
        role.set_perms(form.permissions)
        role_info = role.dump()
    return dict(
        success=True,
        role=role_info,
    )


@app.put('/admin/roles/<int:role_id>')
@perm_accepted(BoPermission.bo_roles_manage)
def edit_role(role_id, form: RoleForm = Depends(), db: Session = Depends(sm.get_db)):
    with sm.transaction_scope():
        role = BoRole.get_or_404(db, role_id)
        role.name = form.name
        role.description = form.description
        role.set_perms(form.permissions)
        data = role.dump()
    return dict(
        success=True,
        role=data,
    )


@app.post('/admin/roles/<int:roles_id>/<string:mode>')
@perm_accepted(BoPermission.bo_users_manage)
def switch_role_mode(roles_id, mode, db: Session = Depends(sm.get_db)):
    role = BoRole.get_or_404(db, roles_id)
    with sm.transaction_scope():
        if mode == 'disable':
            role.disabled_at = datetime.utcnow()
            for user in role.bo_users:
                user.active = False
        else:
            role.disabled_at = None
    return dict(success=True)


@app.get('/admin/permissions')
@perm_accepted(BoPermission.bo_roles_manage)
def list_permissions():
    ret = []
    for group in BoPermissionGroup:
        perms = group.members or []
        ret.append(dict(
            name=group.label,
            perms=[dict(name=p.label, value=p.value) for p in perms])
        )

    return dict(success=True, groups=ret)
