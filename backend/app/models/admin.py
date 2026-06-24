"""Operations backend tables: admin accounts, audit log, moderation queue, and
live-ops config/flags (so axes, weights, slot caps, etc. change without deploy)."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    role: Mapped[str] = mapped_column(String(32), default="moderator")  # moderator/admin/owner


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuidpk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)  # before/after


class ModerationItem(Base, TimestampMixin):
    __tablename__ = "moderation_queue"

    id: Mapped[uuid.UUID] = uuidpk()
    kind: Mapped[str] = mapped_column(String(32))  # persona/report/content
    ref_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/approved/rejected
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class GameConfig(Base, TimestampMixin):
    """Live-ops key/value. Overrides defaults in core/config.py at runtime."""

    __tablename__ = "game_config"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
