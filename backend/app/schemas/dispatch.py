import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.character import CharacterOut


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    type: str
    requirements: dict
    rewards: dict


class DispatchRequest(BaseModel):
    scenario_id: uuid.UUID
    character_ids: list[uuid.UUID] = Field(min_length=1)
    seed: int | None = None  # omit for a random (but recorded) seed


class DispatchResult(BaseModel):
    dispatch_id: uuid.UUID
    outcome: str
    log: dict
    rewards: dict
    characters: list[CharacterOut]  # post-progression state
