import uuid

from pydantic import BaseModel

from app.schemas.character import CharacterOut


class FriendRequestIn(BaseModel):
    handle: str  # target user's handle


class FriendOut(BaseModel):
    friendship_id: uuid.UUID
    user_id: uuid.UUID
    handle: str
    status: str
    direction: str  # incoming / outgoing / friends


class ShareIn(BaseModel):
    target: str = "public"  # "public" or a friend's user_id (uuid string)


class ShareOut(BaseModel):
    token: str
    is_public: bool
    url: str
    card_url: str


class CharacterBefriendIn(BaseModel):
    target_character_id: uuid.UUID


class CharacterFriendResult(BaseModel):
    friend: CharacterOut          # only the other creature is revealed
    remaining_today: int          # befriend quota left for the initiating creature


class SharedCharacterOut(BaseModel):
    name: str | None
    species: str | None
    archetype: str | None
    radar: dict
    trait_tags: list
    persona: str | None
    level: int
    owner_handle: str
