from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from ...db import CRUDMixin, Base


class Settings(CRUDMixin):
    __tablename__ = 'settings'

    key: Mapped[str] = mapped_column(Unicode, unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Unicode)

    def dump(self):
        return dict(
            id=self.id,
            key=self.key,
            value=self.value,
        )
