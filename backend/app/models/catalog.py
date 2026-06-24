"""Data-driven game catalog: radar axes, archetypes, avatar parts. These are
seeded but editable via live-ops so new content ships without a migration."""

import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuidpk


class Axis(Base):
    """Radar axis registry. Adding an axis = inserting a row here."""

    __tablename__ = "axes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    default_value: Mapped[int] = mapped_column(Integer, default=50)


class Archetype(Base):
    __tablename__ = "archetypes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    default_species: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bias: Mapped[dict] = mapped_column(JSONB, default=dict)  # axis_id -> bonus
    allowed_trait_pools: Mapped[list] = mapped_column(JSONB, default=list)


class AvatarPart(Base):
    __tablename__ = "avatar_parts"

    id: Mapped[uuid.UUID] = uuidpk()
    slot: Mapped[str] = mapped_column(String(32))  # body/eyes/hair/outfit/accessory
    part_id: Mapped[str] = mapped_column(String(64))
    style: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unlock_rule: Mapped[dict] = mapped_column(JSONB, default=dict)
