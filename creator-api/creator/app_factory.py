import sys
import redis
import decimal
import json
import contextvars
from datetime import date, datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer

from creator.config import config
from .log import configure_logging

import logging

logger = logging.getLogger(__name__)


app = FastAPI(debug=config.DEBUG)

auth_dep = AuthJWTBearer()

app.mount("/media", StaticFiles(directory="instance"), name="instance")

if not config.SECRET_KEY or not config.AUTHJWT_SECRET_KEY:
    print('SECRET_KEY and AUTHJWT_SECRET_KEY should be set in config')
    sys.exit(1)

# 配置日志
configure_logging(config)


# Redis 配置
# app.state 用于全局存储
redis_client = redis.Redis(
    host=config.REDIS_HOST or 'localhost',
    port=config.REDIS_PORT or 6379,
    db=config.REDIS_DB or 0,
)


try:
    # 发送 PING 命令以测试连接
    response = redis_client.ping()
    if response:
        print("Redis 连接成功")
    else:
        print("Redis 连接失败")
except redis.ConnectionError as e:
    print(f"Redis 连接失败: {e}")


# Redis 依赖项
def get_redis_client():
    return redis_client


def install_app():
    # 安装其他组件
    # from .i18n import install as i18n_install
    # i18n_install(app)

    # from .db import install as db_install
    # db_install()

    from creator import db

    from creator import cli

    from .api import install as api_install

    api_install(app)


def get_full_app():
    install_app()
    return app


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        if isinstance(o, decimal.Decimal):
            if o % 1 == 0:
                return int(o)
            return round(float(o), 2)
        return super().default(o)


# Pydantic model for request validation
class TestModel(BaseModel):
    a: int


@app.on_event("startup")
async def startup_event():
    # 在这里执行启动时的初始化操作
    print("Application startup: initializing resources")
    
    # 初始化 faster-whisper 服务（预加载模型，首次运行会自动下载）
    if config.WHISPER_USE_LOCAL:
        try:
            from creator.api.conversations.whisper_service import get_whisper_service
            logger.info("正在初始化 faster-whisper 服务...")
            logger.info(f"模型配置: {config.WHISPER_MODEL_NAME}, 设备: {config.WHISPER_DEVICE}, 精度: {config.WHISPER_COMPUTE_TYPE}")
            get_whisper_service()  # 触发模型预加载
            logger.info("✅ faster-whisper 服务初始化完成（比 openai-whisper 快 4 倍）")
        except Exception as e:
            logger.error(f"Whisper 服务初始化失败: {str(e)}")
    
    # 例如，连接到数据库或加载配置文件
    # await connect_to_database()


@app.on_event("shutdown")
async def shutdown_event():
    # 在这里执行关闭时的清理操作
    print("Application shutdown: cleaning up resources")
    # 例如，断开数据库连接
    # await disconnect_from_database()


request_context_var = contextvars.ContextVar("request_context")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request.state.from_bo = request.headers.get('from_bo', 'false') == 'true'
    # 将请求对象存储在上下文变量中
    request = request_context_var.set(request)
    try:
        response = await call_next(request)
    finally:
        # 清除上下文变量
        request_context_var.reset(request)
    return response


@app.get("/v1/ping")
async def ping():
    """simple health check"""
    return JSONResponse(content={"success": True, "data": {"success": "ok"}})


@app.post("/v1/test")
async def test(request: Request):
    body = await request.body()
    print(f'request data is "{body.decode("utf-8")}"')
    try:
        data = await request.json()
    except json.JSONDecodeError:
        data = {"error": "cannot decode json"}
    return JSONResponse(content=data)


# Example of handling errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )


# 错误处理
@app.exception_handler(Exception)
async def handle_http_error(request, exc):
    return JSONResponse(status_code=500,
                        content={"message": "Internal server error"})
