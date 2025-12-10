from functools import wraps
import logging

from huey import RedisHuey, crontab

from .config import config


huey = RedisHuey(
    name=config.HUEY_NAME,
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    result_store=False,
    store_errors=False,
)
logger = logging.getLogger()


# convinience crontab definitions
def cron_daily(hour='17', minute='0'):
    return crontab(hour=hour, minute=minute)


def app_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # FastAPI没有Flask的app_context，但你可以在这里初始化一些资源
        return f(*args, **kwargs)
    return wrapper
