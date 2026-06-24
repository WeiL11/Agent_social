import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.user import User
from app.schemas.character import AppearanceUpdate, CharacterOut, CharacterUpdate

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[CharacterOut])
def list_characters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Character).where(Character.owner_id == user.id).order_by(Character.slot)
    )
    return [CharacterOut.model_validate(c) for c in rows]


@router.get("/{character_id}", response_model=CharacterOut)
def get_character(character_id: uuid.UUID, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    char = db.get(Character, character_id)
    if char is None or char.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return CharacterOut.model_validate(char)


@router.put("/{character_id}", response_model=CharacterOut)
def update_character(character_id: uuid.UUID, body: CharacterUpdate,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Edit display name and/or appearance. Both are cosmetic — radar/stats are
    never editable by the player."""
    char = db.get(Character, character_id)
    if char is None or char.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    if body.name is not None:
        char.name = body.name[:48]
    if body.appearance is not None:
        char.appearance = body.appearance
    db.commit()
    db.refresh(char)
    return CharacterOut.model_validate(char)


@router.put("/{character_id}/appearance", response_model=CharacterOut)
def update_appearance(character_id: uuid.UUID, body: AppearanceUpdate,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Cosmetic only — appearance is decoupled from radar/stats by design."""
    char = db.get(Character, character_id)
    if char is None or char.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    char.appearance = body.appearance
    db.commit()
    db.refresh(char)
    return CharacterOut.model_validate(char)
