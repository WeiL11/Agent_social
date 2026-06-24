"""Public SVG rendering of avatar / radar / card by character id. Public so
<img src> works directly (web + app + shared links). These expose only cosmetic
imagery; production can swap to signed URLs if needed."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.character import Character
from app.models.user import User
from app.services.svg import render_avatar, render_card, render_radar

router = APIRouter(prefix="/render/characters", tags=["render"])

SVG = "image/svg+xml"


def _char_dict(c: Character) -> dict:
    return {
        "name": c.name, "species": c.species, "archetype": c.archetype,
        "radar": c.radar, "trait_tags": c.trait_tags, "persona": c.persona,
        "appearance": c.appearance, "level": c.level,
    }


def _load(character_id: uuid.UUID, db: Session) -> Character:
    c = db.get(Character, character_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return c


@router.get("/{character_id}/avatar.svg")
def avatar_svg(character_id: uuid.UUID, db: Session = Depends(get_db)):
    return Response(render_avatar(_char_dict(_load(character_id, db))), media_type=SVG)


@router.get("/{character_id}/radar.svg")
def radar_svg(character_id: uuid.UUID, db: Session = Depends(get_db)):
    return Response(render_radar((_load(character_id, db)).radar or {}), media_type=SVG)


@router.get("/{character_id}/card.svg")
def card_svg(character_id: uuid.UUID, db: Session = Depends(get_db)):
    c = _load(character_id, db)
    owner = db.get(User, c.owner_id)
    return Response(render_card(_char_dict(c), owner.handle if owner else ""), media_type=SVG)
