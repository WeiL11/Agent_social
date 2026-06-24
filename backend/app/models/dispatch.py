import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Scenario(Base, TimestampMixin):
    """#3 dispatch task. requirements is matched against character radar/traits
    by the deterministic rule resolver."""

    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = uuidpk()
    title: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(16), default="solo")  # solo/shared
    requirements: Mapped[dict] = mapped_column(JSONB, default=dict)
    rewards: Mapped[dict] = mapped_column(JSONB, default=dict)
    text_templates: Mapped[dict] = mapped_column(JSONB, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Dispatch(Base, TimestampMixin):
    __tablename__ = "dispatches"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    character_ids: Mapped[list] = mapped_column(JSONB, default=list)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id"))
    seed: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)  # success/fail
    log: Mapped[dict] = mapped_column(JSONB, default=dict)
    rewards_granted: Mapped[dict] = mapped_column(JSONB, default=dict)
