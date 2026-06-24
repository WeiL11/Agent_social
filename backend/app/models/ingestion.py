import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Upload(Base, TimestampMixin):
    """Tracks export / Claude Code ingestion files. file_hash dedupes re-uploads
    so the same data can't be farmed for repeated rewards."""

    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32))  # claude/chatgpt/gemini/claude_code
    source: Mapped[str] = mapped_column(String(32), default="export")
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="received")
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
