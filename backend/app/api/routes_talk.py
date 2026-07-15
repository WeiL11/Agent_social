"""Talk to your own sprite. Every message is stored; every N user messages the
recent text is run through extraction and applied as a personality delta (the
"interact to enrich" loop). Daily-capped; Gemini budget-guarded with template
fallback."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.sprite_talk import SpriteTalk
from app.models.user import User
from app.services.enrichment import apply_enrich
from app.services.extraction import extract_profile
from app.services.facets import rank_facets
from app.services.llm_budget import try_spend_llm
from app.services.sprite_talk import sprite_reply

router = APIRouter(tags=["sprite-talk"])


class TalkIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class TalkMsg(BaseModel):
    role: str
    text: str
    created_at: datetime


class TalkResult(BaseModel):
    reply: TalkMsg
    suggest_mission: bool
    enriched: bool  # did this message trigger a personality delta?


def _owned(db: Session, character_id: uuid.UUID, user: User) -> Character:
    c = db.get(Character, character_id)
    if c is None or c.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    return c


def _char_dict(c: Character) -> dict:
    return {"id": c.id, "name": c.name, "facet": c.facet, "radar": c.radar,
            "trait_tags": c.trait_tags, "persona": c.persona}


@router.post("/characters/{character_id}/talk", response_model=TalkResult)
def talk(character_id: uuid.UUID, body: TalkIn, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    char = _owned(db, character_id, user)

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    sent_today = db.scalar(select(func.count()).select_from(SpriteTalk).where(
        SpriteTalk.character_id == char.id, SpriteTalk.role == "user",
        SpriteTalk.created_at >= today)) or 0
    if sent_today >= settings.sprite_talk_daily_limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"今天聊了 {settings.sprite_talk_daily_limit} 句啦，讓牠休息一下明天再聊！")

    # created_at ties within one exchange (same tx timestamp): 'user' sorts
    # after 'sprite' alphabetically, so desc(created_at), asc(role) is newest-first.
    history_rows = list(db.scalars(select(SpriteTalk).where(
        SpriteTalk.character_id == char.id)
        .order_by(SpriteTalk.created_at.desc(), SpriteTalk.role.asc()).limit(10)))
    history = [{"role": r.role, "text": r.text} for r in reversed(history_rows)]

    llm_key = settings.gemini_api_key if try_spend_llm(db) else None
    out = sprite_reply(_char_dict(char), history, body.message, llm_key)

    db.add(SpriteTalk(character_id=char.id, role="user", text=body.message))
    reply_row = SpriteTalk(character_id=char.id, role="sprite", text=out["text"])
    db.add(reply_row)
    db.commit()
    db.refresh(reply_row)

    # Enrichment loop: every N user messages, distill recent text into a delta.
    enriched = False
    total_user_msgs = db.scalar(select(func.count()).select_from(SpriteTalk).where(
        SpriteTalk.character_id == char.id, SpriteTalk.role == "user")) or 0
    every = settings.sprite_talk_enrich_every
    if every > 0 and total_user_msgs % every == 0:
        recent = list(db.scalars(select(SpriteTalk.text).where(
            SpriteTalk.character_id == char.id, SpriteTalk.role == "user"
        ).order_by(SpriteTalk.created_at.desc()).limit(every)))
        blob = "\n".join(reversed(recent))
        if len(blob) >= 20:
            profile, _engine = extract_profile(blob, None)  # rules: free + enough for deltas
            ranked = rank_facets(profile, threshold=0)
            if ranked:
                apply_enrich(char, ranked[0], active_axis_ids(db), settings.llm_provider)
                db.commit()
                enriched = True

    return TalkResult(
        reply=TalkMsg(role="sprite", text=reply_row.text, created_at=reply_row.created_at),
        suggest_mission=out["suggest_mission"], enriched=enriched,
    )


@router.get("/characters/{character_id}/talk", response_model=list[TalkMsg])
def talk_history(character_id: uuid.UUID, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    char = _owned(db, character_id, user)
    rows = db.scalars(select(SpriteTalk).where(
        SpriteTalk.character_id == char.id)
        .order_by(SpriteTalk.created_at.desc(), SpriteTalk.role.asc()).limit(50))
    return [TalkMsg(role=r.role, text=r.text, created_at=r.created_at) for r in reversed(list(rows))]
