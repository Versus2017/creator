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

@huey.task()
def echo(what):
    logger.info(what)
    return what
