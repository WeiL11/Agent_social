"""Social graph: friendships and character shares. Part of the B-system; reads
character traits/appearance for sharing but never touches A-system progression."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Friendship(Base, TimestampMixin):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("requester_id", "addressee_id", name="uq_friend_pair"),)

    id: Mapped[uuid.UUID] = uuidpk()
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/accepted


class CharacterShare(Base, TimestampMixin):
    """A share grant: either to a specific friend, or public via token (for a
    shareable link / card image)."""

    __tablename__ = "character_shares"

    id: Mapped[uuid.UUID] = uuidpk()
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    shared_with_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    token: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
