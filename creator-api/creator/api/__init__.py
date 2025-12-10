import decimal
from datetime import date, datetime
from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json


router = APIRouter(prefix="/v1")


# noinspection PyShadowingNames
def install(app: FastAPI):
    from .jwt import install
    install()

    from .bo_user import api

    from .users import api
    from .settings import api
    from .wechat import api
    from . import fixtures
    from .media import api
    from .conversations import api

    app.include_router(router)

    # from .errors import handle_http_error
    # for code in default_exceptions:
    #     app.errorhandler(code)(handle_http_error)
    #
    # app.json_encoder = JSONEncoder
