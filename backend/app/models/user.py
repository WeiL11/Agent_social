import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuidpk()
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    auth_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    supabase_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    is_banned: Mapped[bool] = mapped_column(default=False)
