import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: uuid.UUID
    from_me: bool
    body: str
    created_at: datetime
    read: bool


class ConversationOut(BaseModel):
    friend_user_id: uuid.UUID
    handle: str
    last_message: str | None
    last_at: datetime | None
    unread: int
