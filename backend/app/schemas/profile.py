"""Request/response schemas for the self-extraction profile payload. Validation
here is the first line of injection defense: clamp numbers, cap facets."""

import uuid

from pydantic import BaseModel, Field, field_validator

from app.core.constants import MAX_FACETS


def _clamp_radar(v: dict) -> dict:
    out = {}
    for k, val in (v or {}).items():
        try:
            out[str(k)] = max(0, min(100, int(val)))
        except (TypeError, ValueError):
            continue
    return out


class FacetIn(BaseModel):
    facet: str = "learning"
    weight: int = Field(default=0, ge=0, le=100)
    radar: dict[str, int] = Field(default_factory=dict)
    trait_tags: list[str] = Field(default_factory=list)
    species_hint: str | None = None
    summary: str | None = None

    @field_validator("radar", mode="before")
    @classmethod
    def _radar(cls, v):
        return _clamp_radar(v)

    @field_validator("trait_tags", mode="before")
    @classmethod
    def _tags(cls, v):
        if not isinstance(v, list):
            return []
        return [str(t).lower().strip() for t in v][:8]


class SelfExtractProfileIn(BaseModel):
    version: str = "1.0"
    facets: list[FacetIn] = Field(default_factory=list)
    overall_summary: str | None = None

    @field_validator("facets", mode="before")
    @classmethod
    def _cap(cls, v):
        if not isinstance(v, list):
            return []
        return v[:MAX_FACETS]


class GenerateProfileRequest(BaseModel):
    """POST /profiles body. mode picks how to apply against existing characters."""

    source: str = "self_extract"  # self_extract | quiz
    profile: SelfExtractProfileIn
    apply_mode: str = "create_new"  # create_new | enrich_existing
    enrich_character_id: uuid.UUID | None = None
