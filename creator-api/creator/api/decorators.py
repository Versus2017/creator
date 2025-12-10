from copy import deepcopy
from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError


# 验证POST/PUT请求体
def validates(form_cls: BaseModel, form_name: str, obj_id_name=None, form_data=None):
    def decorator(fn):
        async def wrapper(*args, request: Request, **kwargs):
            request_data = form_data or await request.json()
            data = deepcopy(request_data or {})
            data.update({'id': kwargs.get(obj_id_name, None)})
            try:
                form = form_cls(**data)
                form.id = kwargs.get(obj_id_name, None)
            except ValidationError as e:
                message = f"{form_name} validation failed"
                errors = e.errors()
                raise HTTPException(status_code=400, detail={"message": message, "errors": errors})

            return await fn(*args, form=form, **kwargs)
        return wrapper
    return decorator


# 验证GET查询参数
def validates_args(form_cls: BaseModel, form_name: str):
    def decorator(fn):
        async def wrapper(*args, request: Request, **kwargs):
            try:
                form = form_cls(**request.query_params)
            except ValidationError as e:
                message = f"Fetching {form_name} failed"
                errors = e.errors()
                raise HTTPException(status_code=400, detail={"message": message, "errors": errors})

            return await fn(*args, form=form, **kwargs)
        return wrapper
    return decorator


