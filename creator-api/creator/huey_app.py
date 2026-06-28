"""
Huey entrypoint.

import all tasks in this file.

Run the consumer: `huey_consumer creator.huey_app.huey`
"""
from creator.huey_config import huey, logger  # noqa
# import all huey tasks here
from creator.api.wechat import tasks
from creator.api.conversations import tasks as conversation_tasks
from creator.api.users import tasks as user_tasks
from creator.config import config


if config.WHISPER_USE_LOCAL:
    try:
        from creator.api.conversations.whisper_service import get_whisper_service

        logger.info('开始预热 Whisper 模型...')
        whisper_service = get_whisper_service()
        logger.info(
            'Whisper 预热完成: use_local=%s, model_ready=%s, api_ready=%s',
            whisper_service.use_local,
            whisper_service.model is not None,
            whisper_service.api_client is not None,
        )
    except Exception as exc:
        logger.exception('Whisper 预热失败，后续任务会继续重试: %s', exc)

@huey.task()
def echo(what):
    logger.info(what)
    return what
