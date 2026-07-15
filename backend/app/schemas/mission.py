import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.character import CharacterOut


class MissionCreate(BaseModel):
    query_text: str = Field(min_length=4, max_length=500)
    character_id: uuid.UUID | None = None  # default: first active character


class MissionResultItem(BaseModel):
    type: str                      # mutual_goal | sprite_match
    character_id: str
    score: int
    reasons: list[str]
    matched_tags: list[str] = []
    character: CharacterOut | None = None  # hydrated public profile
    waved: bool = False


class MissionOut(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    query_text: str
    kind: str
    tags: list
    status: str
    report: str | None
    items: list[MissionResultItem]
    engine: str | None
    runs_today: int
    last_run_at: datetime | None
    created_at: datetime
