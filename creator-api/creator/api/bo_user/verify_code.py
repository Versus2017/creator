import random
from redis import Redis
from fastapi import Depends, HTTPException
from ..utils import settings
from creator.config import config
from creator.app_factory import get_redis_client

KEY_TPL = 'code-verify:{}'


# 验证码管理类
class CodeVerification:

    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = config.VERIFY_CODE_TTL

    def _get(self, key):
        v = self.redis.get(KEY_TPL.format(key))
        if v:
            return v.decode('utf-8')

    def _set(self, key, value, ex):
        return self.redis.set(KEY_TPL.format(key), value, ex)

    def _del(self, key):
        return self.redis.delete(KEY_TPL.format(key))

    def _gen_code(self):
        return '{:06d}'.format(random.randint(0, 999999))

    def get_or_create(self, key):
        code = self._get(key)
        if not code:
            code = self._gen_code()
            self._set(key, code, self.ttl)
        return code

    def is_code_valid(self, key):
        return True if self._get(key) else False

    def verify(self, key, code, remove_if_match=False):
        if settings.enable_two_fa_debug_mode and code == '888888':
            return True
        print(self._get(key), code)
        matched = self._get(key) == code if code else False
        if remove_if_match and matched:
            self._del(key)
        return matched


redis_client = get_redis_client()
code_verification = CodeVerification(redis_client)
