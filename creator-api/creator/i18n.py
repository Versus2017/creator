from fastapi import FastAPI, Request
from fastapi_babel import BabelMiddleware, BabelConfigs
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# 配置 Babel 的默认语言和支持的语言
BABEL_DEFAULT_LOCALE = 'en'
BABEL_SUPPORTED_LOCALES = ['en', 'es', 'fr']

configs = BabelConfigs(
    ROOT_DIR=__file__,
    BABEL_DEFAULT_LOCALE="en",  # 默认语言
    BABEL_TRANSLATION_DIRECTORY="lang"  # 翻译文件存放的目录
)

# 安装 Babel 中间件
app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=BabelMiddleware(
        app,
        configs
    )
)


@app.middleware("http")
async def get_locale(request: Request, call_next):
    """
    Middleware to determine the best match for supported locales based on the request.
    """
    # # 获取请求中接受的语言
    # accept_language = request.headers.get('accept-language', '')

    # 将最佳匹配语言添加到请求上下文
    request.state.locale = BABEL_DEFAULT_LOCALE

    # 继续处理请求
    response = await call_next(request)
    return response


