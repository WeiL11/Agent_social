"""Owner <-> own-sprite conversation. Talking to your sprite is both the bond
mechanic and the enrichment source: every N user messages, the recent text is
run through the extraction pipeline and applied as a personality delta."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuidpk


class SpriteTalk(Base, TimestampMixin):
    __tablename__ = "sprite_talks"

    id: Mapped[uuid.UUID] = uuidpk()
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(8))  # user | sprite
    text: Mapped[str] = mapped_column(Text)
