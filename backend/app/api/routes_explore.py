"""邂逅 (explore): a sprite goes out, the system picks the most compatible
STRANGER sprite it hasn't met, they have a short auto-chat, and the digest is
shown to the owner — who can then wave at the other owner to become friends.
This is the discovery surface that feeds model-A matchmaking."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import CharacterChat, MatchWave
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.explore import EncounterOut, ExploreResult
from app.services.character_chat import generate_chat
from app.services.matchmaking import compatibility

router = APIRouter(tags=["explore"])


def _today_start() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _owned(db: Session, character_id: uuid.UUID, user: User) -> Character:
    c = db.get(Character, character_id)
    if c is None or c.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return c


def _explored_today(db: Session, character_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(CharacterChat).where(
            CharacterChat.character_a_id == character_id,
            CharacterChat.created_at >= _today_start(),
        )
    ) or 0


def _met_ids(db: Session, character_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(
        select(CharacterChat.character_a_id, CharacterChat.character_b_id).where(
            or_(CharacterChat.character_a_id == character_id,
                CharacterChat.character_b_id == character_id)
        )
    )
    met: set[uuid.UUID] = set()
    for a, b in rows:
        met.add(b if a == character_id else a)
    return met


def _as_dict(c: Character) -> dict:
    return {"id": c.id, "name": c.name, "facet": c.facet,
            "radar": c.radar, "trait_tags": c.trait_tags}


@router.post("/characters/{character_id}/explore", response_model=ExploreResult)
def explore(character_id: uuid.UUID, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    limit = settings.character_explore_daily_limit
    used = _explored_today(db, me.id)
    if used >= limit:
        return ExploreResult(encounter=None, remaining_today=0,
                             message=f"今天已經出門 {limit} 次了，明天再來吧！")

    met = _met_ids(db, me.id)
    candidates = list(db.scalars(
        select(Character).join(User, Character.owner_id == User.id).where(
            User.discoverable.is_(True), User.is_banned.is_(False),
            Character.owner_id != user.id, Character.status == "active",
        )
    ))
    candidates = [c for c in candidates if c.id not in met]
    if not candidates:
        return ExploreResult(encounter=None, remaining_today=limit - used,
                             message="外面靜悄悄的，沒遇到新朋友。晚點再試試！")

    axis_ids = active_axis_ids(db)
    scored = [
        (compatibility(_as_dict(me), _as_dict(c), settings.match_weights, axis_ids), c)
        for c in candidates
    ]
    scored.sort(key=lambda t: t[0]["score"], reverse=True)
    comp, other = scored[0]

    chat_res = generate_chat(_as_dict(me), _as_dict(other),
                             settings.character_chat_turns, settings.llm_provider)
    chat = CharacterChat(character_a_id=me.id, character_b_id=other.id,
                         transcript=chat_res["transcript"], summary=chat_res["summary"])
    db.add(chat)
    db.commit()
    db.refresh(chat)

    waved = db.scalar(select(MatchWave).where(
        MatchWave.from_user_id == user.id, MatchWave.to_user_id == other.owner_id)) is not None

    return ExploreResult(
        encounter=EncounterOut(
            chat_id=chat.id,
            my_character=CharacterOut.model_validate(me),
            other_character=CharacterOut.model_validate(other),
            compatibility=comp["score"], reasons=comp["reasons"],
            transcript=chat.transcript, summary=chat.summary,
            created_at=chat.created_at, waved=waved,
        ),
        remaining_today=limit - used - 1,
        message="遇到了一位新朋友！",
    )


@router.get("/me/encounters", response_model=list[EncounterOut])
def my_encounters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """今日邂逅 digest across all my sprites, newest first."""
    mine = {c.id: c for c in db.scalars(
        select(Character).where(Character.owner_id == user.id))}
    if not mine:
        return []
    chats = db.scalars(
        select(CharacterChat).where(
            or_(CharacterChat.character_a_id.in_(mine.keys()),
                CharacterChat.character_b_id.in_(mine.keys())),
            CharacterChat.created_at >= _today_start(),
        ).order_by(CharacterChat.created_at.desc())
    )
    waved_to = set(db.scalars(
        select(MatchWave.to_user_id).where(MatchWave.from_user_id == user.id)))
    axis_ids = active_axis_ids(db)

    out: list[EncounterOut] = []
    for ch in chats:
        my_id = ch.character_a_id if ch.character_a_id in mine else ch.character_b_id
        other_id = ch.character_b_id if ch.character_a_id in mine else ch.character_a_id
        if other_id in mine:  # my two sprites chatting each other — skip digest
            continue
        other = db.get(Character, other_id)
        if other is None:
            continue
        comp = compatibility(_as_dict(mine[my_id]), _as_dict(other),
                             settings.match_weights, axis_ids)
        out.append(EncounterOut(
            chat_id=ch.id,
            my_character=CharacterOut.model_validate(mine[my_id]),
            other_character=CharacterOut.model_validate(other),
            compatibility=comp["score"], reasons=comp["reasons"],
            transcript=ch.transcript, summary=ch.summary,
            created_at=ch.created_at, waved=other.owner_id in waved_to,
        ))
    return out
