"""Character-level friends: a creature makes its own friends (rate-limited per
day). Listing reveals ONLY the other creature — never its owner or roster."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import CharacterFriendship
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.social import CharacterBefriendIn, CharacterFriendResult

router = APIRouter(prefix="/characters/{character_id}/friends", tags=["character-friends"])


def _owned(db: Session, character_id: uuid.UUID, user: User) -> Character:
    char = db.get(Character, character_id)
    if char is None or char.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return char


def _get_pair(db: Session, a: uuid.UUID, b: uuid.UUID) -> CharacterFriendship | None:
    CF = CharacterFriendship
    return db.scalar(
        select(CF).where(
            or_(
                (CF.character_a_id == a) & (CF.character_b_id == b),
                (CF.character_a_id == b) & (CF.character_b_id == a),
            )
        )
    )


def _made_today(db: Session, character_id: uuid.UUID) -> int:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count()).select_from(CharacterFriendship).where(
            CharacterFriendship.character_a_id == character_id,
            CharacterFriendship.created_at >= start,
        )
    ) or 0


@router.post("", response_model=CharacterFriendResult)
def befriend(character_id: uuid.UUID, body: CharacterBefriendIn,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    if body.target_character_id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "a creature cannot befriend itself")
    target = db.get(Character, body.target_character_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "target character not found")
    if _get_pair(db, me.id, target.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "already friends")

    limit = settings.character_friend_daily_limit
    if _made_today(db, me.id) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"daily limit reached ({limit} new friends/day)")

    db.add(CharacterFriendship(character_a_id=me.id, character_b_id=target.id))
    db.commit()
    remaining = max(0, limit - _made_today(db, me.id))
    return CharacterFriendResult(friend=CharacterOut.model_validate(target), remaining_today=remaining)


@router.get("", response_model=list[CharacterOut])
def list_character_friends(character_id: uuid.UUID, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    rows = db.scalars(
        select(CharacterFriendship).where(
            or_(CharacterFriendship.character_a_id == me.id,
                CharacterFriendship.character_b_id == me.id)
        )
    )
    friends: list[CharacterOut] = []
    for fr in rows:
        other_id = fr.character_b_id if fr.character_a_id == me.id else fr.character_a_id
        other = db.get(Character, other_id)
        if other is not None:  # only the other creature is exposed
            friends.append(CharacterOut.model_validate(other))
    return friends


@router.delete("/{other_character_id}")
def unfriend(character_id: uuid.UUID, other_character_id: uuid.UUID,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    fr = _get_pair(db, me.id, other_character_id)
    if fr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not friends")
    db.delete(fr)
    db.commit()
    return {"deleted": str(fr.id)}
