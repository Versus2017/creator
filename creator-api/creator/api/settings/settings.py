from .fields import *
from .base import SettingsBase


class Settings(SettingsBase):
    """Live settings.

    Define here, use `dotalk.api.utils.settings`.

    Unlike hard static Flask config, settings are stored in database and loaded
    on every request, suitable for frequently-changed flexible global settings.
    """
    enable_two_fa_login = BooleanField(
        False, name='启用 2fa 登录',
        desc='启用后，后台用户登录需要进行手机验证码二次认证', type='switch')
    enable_two_fa_debug_mode = BooleanField(
        False, name='启用 2fa Debug 模式',
        desc='启用后，888888 可用做万能验证码', type='switch')
    wechat_event_token = StringField(
        '', name='微信验证 Token',
        desc='用于验证微信通知发送地址的 token', type='input'
    )
