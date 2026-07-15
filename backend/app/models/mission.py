"""Missions: the sprite as a purposeful social agent. The owner states a goal
("我想找一起跑步的人"); the sprite searches IN-PLATFORM (other users' missions +
sprite profiles) and reports back. External search (Reddit / web) is a later
phase. Results are a JSONB snapshot so reports stay stable as data changes."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Mission(Base, TimestampMixin):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    query_text: Mapped[str] = mapped_column(Text)
    # find_people / find_group / find_experience / auto
    kind: Mapped[str] = mapped_column(String(24), default="auto")
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/archived
    # {items: [...], report: str, engine: str, ran_at: iso, run_dates: [iso]}
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
