"""B-system: community scoring, seasons, shared events, achievements, cohorts.
Deliberately decoupled from A-system progression (xp/level) — these tables read
character traits but never the growth stats."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = uuidpk()
    name: Mapped[str] = mapped_column(String(64))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ruleset: Mapped[dict] = mapped_column(JSONB, default=dict)


class CommunityScore(Base, TimestampMixin):
    __tablename__ = "community_scores"

    id: Mapped[uuid.UUID] = uuidpk()
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    uniqueness: Mapped[float] = mapped_column(Float, default=0.0)
    achievements: Mapped[dict] = mapped_column(JSONB, default=dict)


class PopulationStat(Base, TimestampMixin):
    """Periodic snapshot of the radar distribution + trait frequencies used to
    compute uniqueness."""

    __tablename__ = "population_stats"

    id: Mapped[uuid.UUID] = uuidpk()
    snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)


class SharedEvent(Base, TimestampMixin):
    __tablename__ = "shared_events"

    id: Mapped[uuid.UUID] = uuidpk()
    title: Mapped[str] = mapped_column(String(128))
    requirement: Mapped[dict] = mapped_column(JSONB, default=dict)
    rewards: Mapped[dict] = mapped_column(JSONB, default=dict)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    aggregate_progress: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open/settled


class EventContribution(Base, TimestampMixin):
    __tablename__ = "event_contributions"

    id: Mapped[uuid.UUID] = uuidpk()
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shared_events.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    contribution: Mapped[float] = mapped_column(Float, default=0.0)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict)


class UserAchievement(Base, TimestampMixin):
    __tablename__ = "user_achievements"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_id: Mapped[str] = mapped_column(ForeignKey("achievements.id"))


class Cohort(Base, TimestampMixin):
    __tablename__ = "cohorts"

    id: Mapped[uuid.UUID] = uuidpk()
    name: Mapped[str] = mapped_column(String(64))
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict)  # archetype / trait based
    discord_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = uuidpk()
    cohort_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohorts.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = uuidpk()
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type: Mapped[str] = mapped_column(String(32))  # character/post/user
    target_id: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
