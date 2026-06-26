import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatStartIn(BaseModel):
    with_character_id: uuid.UUID


class ChatLine(BaseModel):
    speaker: str
    character_id: uuid.UUID | None = None
    text: str


class CharacterChatOut(BaseModel):
    id: uuid.UUID
    transcript: list[ChatLine]
    summary: str | None
    created_at: datetime


class CharacterChatSummary(BaseModel):
    id: uuid.UUID
    summary: str | None
    created_at: datetime
