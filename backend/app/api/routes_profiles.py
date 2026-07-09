"""POST /profiles — the core onboarding flow: validated self-extract/quiz profile
-> facet ranking -> rule-based character generation (respecting the slot cap),
or enrich an existing character. LLM (if configured) only writes persona text."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.admin import ModerationItem
from app.models.character import Character, PersonalityProfile
from app.models.user import User
from app.schemas.character import CharacterOut, GenerateResult
from app.schemas.profile import GenerateProfileRequest
from app.services.deid import scrub
from app.services.extraction import extract_profile
from app.services.facets import rank_facets
from app.services.generation import generate_character_fields
from app.services.llm_budget import try_spend_llm

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ExtractRequest(BaseModel):
    text: str = Field(min_length=20, max_length=200_000)  # raw conversation text
    apply_mode: str = "create_new"  # create_new | enrich_existing
    enrich_character_id: uuid.UUID | None = None


class ExtractResult(GenerateResult):
    engine: str  # "gemini" | "rules"


@router.post("/extract", response_model=ExtractResult)
def extract_and_generate(
    body: ExtractRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The real soul-pipeline: paste raw AI-conversation text -> de-identify ->
    extract personality (Gemini if configured + within budget, rules otherwise)
    -> characters."""
    llm_key = settings.gemini_api_key if try_spend_llm(db) else None
    profile, engine = extract_profile(body.text, llm_key)
    inner = GenerateProfileRequest(
        source="self_extract", profile=profile,
        apply_mode=body.apply_mode, enrich_character_id=body.enrich_character_id,
    )
    result = create_profile(inner, db=db, user=user)
    return ExtractResult(**result.model_dump(), engine=engine)


@router.post("", response_model=GenerateResult)
def create_profile(
    body: GenerateProfileRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ranked = rank_facets(body.profile, settings.facet_weight_threshold)
    if not ranked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no usable facets in profile")

    axis_ids = active_axis_ids(db)

    # Enrich path: nudge one existing character with the strongest facet (delta),
    # never regenerate from scratch (avoids personality drift).
    if body.apply_mode == "enrich_existing":
        if not body.enrich_character_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "enrich_character_id required")
        char = db.get(Character, body.enrich_character_id)
        if char is None or char.owner_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
        fields = generate_character_fields(ranked[0], axis_ids, settings.llm_provider)
        merged = dict(char.radar or {})
        for axis, val in fields["radar"].items():  # average toward the new signal
            merged[axis] = int(((merged.get(axis, val)) + val) / 2)
        char.radar = merged
        char.trait_tags = sorted(set((char.trait_tags or []) + fields["trait_tags"]))
        _store_profile(db, user, body.source, ranked[0])
        db.commit()
        db.refresh(char)
        return GenerateResult(created=[CharacterOut.model_validate(char)], skipped_facets=[],
                              slot_cap=settings.character_slot_cap)

    # Create path: fill remaining slots, report facets dropped by the cap.
    used = db.scalar(
        select(func.count()).select_from(Character).where(
            Character.owner_id == user.id, Character.status == "active"
        )
    ) or 0
    remaining = max(0, settings.character_slot_cap - used)

    created: list[Character] = []
    skipped: list[str] = []
    for i, facet in enumerate(ranked):
        if i >= remaining:
            skipped.append(facet.facet)
            continue
        profile = _store_profile(db, user, body.source, facet)
        fields = generate_character_fields(facet, axis_ids, settings.llm_provider)
        char = Character(owner_id=user.id, slot=used + len(created),
                         source_profile_id=profile.id, **fields)
        db.add(char)
        db.flush()
        db.add(ModerationItem(kind="persona", ref_id=str(char.id),
                              payload={"persona": char.persona}))
        created.append(char)

    db.commit()
    for c in created:
        db.refresh(c)
    return GenerateResult(
        created=[CharacterOut.model_validate(c) for c in created],
        skipped_facets=skipped,
        slot_cap=settings.character_slot_cap,
    )


def _store_profile(db: Session, user: User, source: str, facet) -> PersonalityProfile:
    profile = PersonalityProfile(
        user_id=user.id,
        source=source,
        facet=facet.facet,
        weight=facet.weight,
        raw_features={"radar": facet.radar, "trait_tags": facet.trait_tags,
                      "species_hint": facet.species_hint},
        summary=scrub(facet.summary),
    )
    db.add(profile)
    db.flush()
    return profile
