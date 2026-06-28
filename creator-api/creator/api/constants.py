from .utils import IntEnum, Enum


class BoPermission(Enum):
    misc_sensitive_info_view = 'misc_sensitive_info_view'

    # 系统级别
    live_settings_manage = 'live_settings_manage'

    # 后台用户
    bo_roles_view = 'bo_roles_view'
    bo_roles_manage = 'bo_roles_manage'
    bo_users_view = 'bo_users_view'
    bo_users_manage = 'bo_users_manage'
    bo_users_wechat_bind_manage = 'bo_users_wechat_bind_manage'


BoPermission.misc_sensitive_info_view.label = 'Sensitive Info View'  # '敏感用户信息 - 查看'
BoPermission.live_settings_manage.label = 'Settings Manage'  # '管理系统配置'
BoPermission.bo_roles_view.label = 'Roles View'  # '查看角色'
BoPermission.bo_roles_manage.label = 'Roles Manage'  # '管理角色'
BoPermission.bo_users_view.label = 'Users View'  # '查看用户列表'
BoPermission.bo_users_manage.label = 'Users Manage'  # '管理用户'
BoPermission.bo_users_wechat_bind_manage.label = 'Users WeChat Bind Manage'  # '管理微信账户绑定'


# 绑定了后台用户的微信用户牵扯到的权限，请设置 use_in_wechat = True
# BoPermission.wechat_workbench_xxx.use_in_wechat = True


class BoPermissionGroup(IntEnum):
    system = 100
    bo_user = 200


BoPermissionGroup.system.label = 'System'  # '系统级别'
BoPermissionGroup.bo_user.label = 'User'  # '后台用户'

BoPermissionGroup.system.members = [
    BoPermission.live_settings_manage
]

BoPermissionGroup.bo_user.members = [
    BoPermission.misc_sensitive_info_view,
    BoPermission.bo_roles_view,
    BoPermission.bo_roles_manage,
    BoPermission.bo_users_view,
    BoPermission.bo_users_manage,
    BoPermission.bo_users_wechat_bind_manage,
]
