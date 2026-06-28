from typing import Optional
from pydantic import BaseModel


class BaseFilterForm(BaseModel):
    keyword: Optional[str] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 10
