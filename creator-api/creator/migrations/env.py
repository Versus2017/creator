from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import logging

# 导入你的数据库模块
from creator.db import sm, Base, install

install()

# 解析 Alembic 配置文件
config = context.config

# 配置日志
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# 设置 SQLAlchemy URL
config.set_main_option('sqlalchemy.url', str(sm.engine.url))

# 目标元数据
target_metadata = Base.metadata


def run_migrations_offline():
    """以离线模式运行迁移。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """以在线模式运行迁移。"""
    # 防止在没有模式更改时生成自动迁移
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    connectable = sm.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
        )

        try:
            with context.begin_transaction():
                context.run_migrations()
        except Exception as e:
            logger.exception('Migrate failed', exc_info=e)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()