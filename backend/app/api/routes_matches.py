"""Matchmaking (model A: persona as matchmaker connecting real people).
GET /matches recommends compatible personas; waving expresses interest, and a
mutual wave bridges the two humans into owner-friends (consent-gated)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import Friendship, MatchWave
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.matchmaking import MatchOut, WaveIn, WaveResult
from app.services.matchmaking import compatibility

router = APIRouter(prefix="/matches", tags=["matchmaking"])


def _as_dict(c: Character) -> dict:
    return {"radar": c.radar, "trait_tags": c.trait_tags, "facet": c.facet}


@router.get("", response_model=list[MatchOut])
def get_matches(limit: int = 10, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    mine = list(db.scalars(
        select(Character).where(Character.owner_id == user.id, Character.status == "active")
    ))
    if not mine:
        return []
    axis_ids = active_axis_ids(db)

    candidates = db.scalars(
        select(Character).join(User, Character.owner_id == User.id).where(
            User.discoverable.is_(True),
            User.is_banned.is_(False),
            Character.owner_id != user.id,
            Character.status == "active",
        )
    )
    waved_to = set(db.scalars(
        select(MatchWave.to_user_id).where(MatchWave.from_user_id == user.id)
    ))

    results: list[MatchOut] = []
    for cand in candidates:
        best = None
        for m in mine:
            comp = compatibility(_as_dict(m), _as_dict(cand), settings.match_weights, axis_ids)
            if best is None or comp["score"] > best["score"]:
                best = {**comp, "my_character_id": m.id}
        results.append(MatchOut(
            their_character=CharacterOut.model_validate(cand),
            my_character_id=best["my_character_id"],
            score=best["score"], reasons=best["reasons"],
            waved=cand.owner_id in waved_to,
        ))
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


def _accepted_count(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(Friendship).where(
            Friendship.status == "accepted",
            or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
        )
    ) or 0


@router.post("/{their_character_id}/wave", response_model=WaveResult)
def wave(their_character_id: uuid.UUID, body: WaveIn | None = None,
         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target = db.get(Character, their_character_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    to_user = target.owner_id
    if to_user == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot wave at your own character")

    from_char = db.scalar(
        select(Character).where(Character.owner_id == user.id, Character.status == "active").limit(1)
    )
    if body and body.from_character_id:
        picked = db.get(Character, body.from_character_id)
        if picked is None or picked.owner_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "from_character not found")
        from_char = picked
    if from_char is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "you have no character to wave with")

    # record my wave (idempotent on the pair)
    mine_wave = db.scalar(
        select(MatchWave).where(MatchWave.from_user_id == user.id, MatchWave.to_user_id == to_user)
    )
    if mine_wave is None:
        db.add(MatchWave(from_user_id=user.id, to_user_id=to_user,
                         from_character_id=from_char.id, to_character_id=their_character_id))
        db.commit()

    # mutual? -> bridge into owner-friends
    reverse = db.scalar(
        select(MatchWave).where(MatchWave.from_user_id == to_user, MatchWave.to_user_id == user.id)
    )
    if not reverse:
        return WaveResult(matched=False)

    fr = db.scalar(
        select(Friendship).where(
            or_(
                (Friendship.requester_id == user.id) & (Friendship.addressee_id == to_user),
                (Friendship.requester_id == to_user) & (Friendship.addressee_id == user.id),
            )
        )
    )
    cap = settings.owner_friend_cap
    if fr is None:
        if _accepted_count(db, user.id) >= cap or _accepted_count(db, to_user) >= cap:
            raise HTTPException(status.HTTP_409_CONFLICT, f"owner friend limit reached ({cap})")
        fr = Friendship(requester_id=user.id, addressee_id=to_user, status="accepted")
        db.add(fr)
    else:
        fr.status = "accepted"
    db.commit()
    db.refresh(fr)
    return WaveResult(matched=True, friendship_id=fr.id)
