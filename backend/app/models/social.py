"""Social graph: two distinct friend layers + character shares.

- Friendship       = OWNER level (user <-> user). The "normal" add-friend, capped
  at settings.owner_friend_cap. Lets you see all characters that user manages.
- CharacterFriendship = CHARACTER level (creature <-> creature). A creature makes
  its own friends, rate-limited to settings.character_friend_daily_limit/day.
  Viewing it reveals only the other creature, not its owner/roster.

Part of the B-system; never touches A-system progression."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class Friendship(Base, TimestampMixin):
    """Owner-level (user <-> user) friendship."""

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


class CharacterFriendship(Base, TimestampMixin):
    """Character-level (creature <-> creature) friendship. character_a is the
    initiator; the day's quota is counted against the initiator only. Mutual:
    friends-of-X = rows where X is character_a OR character_b."""

    __tablename__ = "character_friendships"
    __table_args__ = (UniqueConstraint("character_a_id", "character_b_id", name="uq_char_friend_pair"),)

    id: Mapped[uuid.UUID] = uuidpk()
    character_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    character_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )


class MatchWave(Base, TimestampMixin):
    """A 'wave' = expressing interest after a match. When both users have waved
    at each other, they become owner-friends (consent-gated bot->real bridge)."""

    __tablename__ = "match_waves"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_wave_pair"),)

    id: Mapped[uuid.UUID] = uuidpk()
    from_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    to_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    from_character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    to_character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))


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
