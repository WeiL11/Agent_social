import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.character import CharacterOut
from app.schemas.character_chat import ChatLine


class EncounterOut(BaseModel):
    """One 邂逅: my sprite met a stranger sprite. Shows the other sprite's public
    profile + the short chat + summary; the other OWNER's identity stays hidden
    until a mutual wave."""

    chat_id: uuid.UUID
    my_character: CharacterOut
    other_character: CharacterOut
    compatibility: int
    reasons: list[str]
    transcript: list[ChatLine]
    summary: str | None
    created_at: datetime
    waved: bool  # did I already wave at that sprite's owner?


class ExploreResult(BaseModel):
    encounter: EncounterOut | None
    remaining_today: int
    message: str
