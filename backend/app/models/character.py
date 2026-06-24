import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class PersonalityProfile(Base, TimestampMixin):
    """One de-identified personality side-profile derived from a source. A user
    can have several (one per facet) which seed distinct characters."""

    __tablename__ = "personality_profiles"

    id: Mapped[uuid.UUID] = uuidpk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(32))  # quiz/self_extract/claude_code/export
    facet: Mapped[str | None] = mapped_column(String(32), nullable=True)
    weight: Mapped[int] = mapped_column(Integer, default=0)
    raw_features: Mapped[dict] = mapped_column(JSONB, default=dict)  # radar + trait_tags + hints
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class Character(Base, TimestampMixin):
    """A-system entity: stats grow via dispatch; appearance is cosmetic and
    decoupled from stats. lineage hook reserved for future inheritance."""

    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = uuidpk()
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slot: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str | None] = mapped_column(String(48), nullable=True)  # player-editable display name
    species: Mapped[str | None] = mapped_column(String(32), nullable=True)
    archetype: Mapped[str | None] = mapped_column(ForeignKey("archetypes.id"), nullable=True)
    facet: Mapped[str | None] = mapped_column(String(32), nullable=True)
    radar: Mapped[dict] = mapped_column(JSONB, default=dict)  # axis_id -> 0..100
    trait_tags: Mapped[list] = mapped_column(JSONB, default=list)
    persona: Mapped[str | None] = mapped_column(Text, nullable=True)
    appearance: Mapped[dict] = mapped_column(JSONB, default=dict)  # slot -> part_id
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/retired
    parent_character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id"), nullable=True
    )  # lineage hook (inheritance not yet implemented)
    source_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("personality_profiles.id"), nullable=True
    )
