import uuid

from pydantic import BaseModel, ConfigDict


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slot: int
    name: str | None
    species: str | None
    archetype: str | None
    facet: str | None
    radar: dict
    trait_tags: list
    persona: str | None
    appearance: dict
    level: int
    xp: int
    status: str


class AppearanceUpdate(BaseModel):
    appearance: dict  # slot -> part_id (cosmetic only, never touches radar)


class CharacterUpdate(BaseModel):
    name: str | None = None
    appearance: dict | None = None  # cosmetic only


class GenerateResult(BaseModel):
    created: list[CharacterOut]
    skipped_facets: list[str]  # facets dropped due to slot cap
    slot_cap: int
