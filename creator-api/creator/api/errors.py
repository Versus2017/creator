from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from .wechat import wechat


async def handle_http_error(request: Request, exc: Exception):
    is_internal_api = '/v1/internal' in str(request.url)
    extra = {}
    if isinstance(exc, HTTPException):
        if exc.status_code == 400:
            desc = exc.detail
        elif exc.status_code == 401:
            if is_internal_api:
                desc = '请提供 api key'
            else:
                desc = '无法获取帐号信息，<br>请重新打开服务'
                extra['redirect_url'] = wechat.oauth_url
        elif exc.status_code == 403:
            desc = '您无权进行该操作'
        elif exc.status_code == 404:
            desc = '找不到该内容'
        elif exc.status_code == 405:
            desc = '请求方法不支持'
        else:
            desc = '服务出错，请稍后再试'
        status_code = exc.status_code
    else:
        desc = '服务出错，请稍后再试'
        status_code = 500
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"message": desc},
            **extra,
        }
    )