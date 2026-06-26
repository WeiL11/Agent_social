"""Character<->character short auto-chat (model B). Gated to character-friends,
rate-limited per day to bound cost. Stores a brief transcript + summary."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import CharacterChat, CharacterFriendship
from app.models.user import User
from app.schemas.character_chat import (
    CharacterChatOut,
    CharacterChatSummary,
    ChatStartIn,
)
from app.services.character_chat import generate_chat

router = APIRouter(tags=["character-chat"])


def _owned(db: Session, character_id: uuid.UUID, user: User) -> Character:
    c = db.get(Character, character_id)
    if c is None or c.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return c


def _are_char_friends(db: Session, a: uuid.UUID, b: uuid.UUID) -> bool:
    CF = CharacterFriendship
    return db.scalar(
        select(CF).where(
            or_((CF.character_a_id == a) & (CF.character_b_id == b),
                (CF.character_a_id == b) & (CF.character_b_id == a))
        )
    ) is not None


def _as_dict(c: Character) -> dict:
    return {"id": c.id, "name": c.name, "facet": c.facet,
            "radar": c.radar, "trait_tags": c.trait_tags}


def _started_today(db: Session, character_id: uuid.UUID) -> int:
    start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count()).select_from(CharacterChat).where(
            CharacterChat.character_a_id == character_id,
            CharacterChat.created_at >= start)
    ) or 0


@router.post("/characters/{character_id}/chats", response_model=CharacterChatOut)
def start_chat(character_id: uuid.UUID, body: ChatStartIn, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    other = db.get(Character, body.with_character_id)
    if other is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "other character not found")
    if other.id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "a creature cannot chat with itself")
    if not _are_char_friends(db, me.id, other.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "creatures must be friends to chat")

    limit = settings.character_chat_daily_limit
    if _started_today(db, me.id) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"daily chat limit reached ({limit})")

    result = generate_chat(_as_dict(me), _as_dict(other),
                           settings.character_chat_turns, settings.llm_provider)
    chat = CharacterChat(character_a_id=me.id, character_b_id=other.id,
                         transcript=result["transcript"], summary=result["summary"])
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return CharacterChatOut(id=chat.id, transcript=chat.transcript, summary=chat.summary,
                            created_at=chat.created_at)


@router.get("/characters/{character_id}/chats", response_model=list[CharacterChatSummary])
def list_chats(character_id: uuid.UUID, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    me = _owned(db, character_id, user)
    rows = db.scalars(
        select(CharacterChat).where(
            or_(CharacterChat.character_a_id == me.id, CharacterChat.character_b_id == me.id)
        ).order_by(CharacterChat.created_at.desc())
    )
    return [CharacterChatSummary(id=c.id, summary=c.summary, created_at=c.created_at) for c in rows]


@router.get("/character-chats/{chat_id}", response_model=CharacterChatOut)
def get_chat(chat_id: uuid.UUID, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    chat = db.get(CharacterChat, chat_id)
    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chat not found")
    a = db.get(Character, chat.character_a_id)
    b = db.get(Character, chat.character_b_id)
    if user.id not in {getattr(a, "owner_id", None), getattr(b, "owner_id", None)}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not your chat")
    return CharacterChatOut(id=chat.id, transcript=chat.transcript, summary=chat.summary,
                            created_at=chat.created_at)
