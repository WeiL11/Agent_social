import uuid

from pydantic import BaseModel

from app.schemas.character import CharacterOut


class MatchOut(BaseModel):
    their_character: CharacterOut   # persona shown; human identity hidden until mutual wave
    my_character_id: uuid.UUID      # which of my characters resonates most
    score: int                      # 0..100 compatibility
    reasons: list[str]
    waved: bool                     # have I already waved at this person?


class WaveIn(BaseModel):
    from_character_id: uuid.UUID | None = None  # defaults to my best-matching character


class WaveResult(BaseModel):
    matched: bool                   # both sides waved -> now owner-friends
    friendship_id: uuid.UUID | None = None


class MeOut(BaseModel):
    handle: str
    discoverable: bool


class MeUpdate(BaseModel):
    discoverable: bool
