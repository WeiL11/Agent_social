"""Missions: tell your sprite what you're looking for; it searches in-platform
(mutual goals + sprite profiles) and reports back. Connecting stays on the
existing wave bridge (owner identity hidden until mutual wave)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.mission import Mission
from app.models.social import MatchWave
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.mission import MissionCreate, MissionOut, MissionResultItem
from app.services.llm_budget import try_spend_llm
from app.services.missions import match_mission, parse_mission, report_text

router = APIRouter(prefix="/missions", tags=["missions"])


def _char_dict(c: Character) -> dict:
    return {"id": c.id, "owner_id": c.owner_id, "name": c.name, "facet": c.facet,
            "radar": c.radar, "trait_tags": c.trait_tags, "persona": c.persona}


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _runs_today(m: Mission) -> int:
    return sum(1 for d in (m.results or {}).get("run_dates", []) if d.startswith(_today()))


def _run(db: Session, m: Mission, user: User) -> None:
    my_char = db.get(Character, m.character_id)
    axis_ids = active_axis_ids(db)

    stranger_chars = [
        _char_dict(c) for c in db.scalars(
            select(Character).join(User, Character.owner_id == User.id).where(
                User.discoverable.is_(True), User.is_banned.is_(False),
                Character.owner_id != user.id, Character.status == "active",
            )
        )
    ]
    other_missions = []
    rows = db.execute(
        select(Mission, Character).join(Character, Mission.character_id == Character.id)
        .join(User, Mission.user_id == User.id)
        .where(Mission.status == "active", Mission.user_id != user.id,
               User.discoverable.is_(True), User.is_banned.is_(False))
    )
    for om, oc in rows:
        other_missions.append({"tags": om.tags, "query_text": om.query_text,
                               "character": _char_dict(oc)})

    items = match_mission(
        {"tags": m.tags, "query_text": m.query_text}, _char_dict(my_char),
        other_missions, stranger_chars, settings.match_weights, axis_ids,
        limit=settings.mission_result_limit,
    )
    report = report_text(my_char.name or "小精靈", m.query_text, items)

    prev = dict(m.results or {})
    run_dates = prev.get("run_dates", []) + [datetime.now(UTC).isoformat()]
    m.results = {"items": items, "report": report,
                 "engine": prev.get("engine", "rules"), "run_dates": run_dates}
    m.last_run_at = datetime.now(UTC)
    db.commit()
    db.refresh(m)


def _out(db: Session, m: Mission, user: User) -> MissionOut:
    res = m.results or {}
    waved_to = set(db.scalars(select(MatchWave.to_user_id).where(MatchWave.from_user_id == user.id)))
    items = []
    for it in res.get("items", []):
        char = db.get(Character, uuid.UUID(it["character_id"]))
        items.append(MissionResultItem(
            **it,
            character=CharacterOut.model_validate(char) if char else None,
            waved=(char is not None and char.owner_id in waved_to),
        ))
    return MissionOut(
        id=m.id, character_id=m.character_id, query_text=m.query_text, kind=m.kind,
        tags=m.tags, status=m.status, report=res.get("report"), items=items,
        engine=res.get("engine"), runs_today=_runs_today(m),
        last_run_at=m.last_run_at, created_at=m.created_at,
    )


@router.post("", response_model=MissionOut)
def create_mission(body: MissionCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    active = db.scalar(select(func.count()).select_from(Mission).where(
        Mission.user_id == user.id, Mission.status == "active")) or 0
    if active >= settings.mission_active_cap:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"最多同時 {settings.mission_active_cap} 個任務，先封存一些吧")

    if body.character_id:
        char = db.get(Character, body.character_id)
        if char is None or char.owner_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")
    else:
        char = db.scalar(select(Character).where(
            Character.owner_id == user.id, Character.status == "active"
        ).order_by(Character.slot).limit(1))
        if char is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "先生成一隻小精靈")

    llm_key = settings.gemini_api_key if try_spend_llm(db) else None
    parsed, engine = parse_mission(body.query_text, llm_key)

    m = Mission(user_id=user.id, character_id=char.id, query_text=body.query_text,
                kind=parsed["kind"], tags=parsed["tags"], results={"engine": engine})
    db.add(m)
    db.commit()
    db.refresh(m)
    _run(db, m, user)  # first run immediately
    return _out(db, m, user)


@router.get("", response_model=list[MissionOut])
def list_missions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Mission).where(
        Mission.user_id == user.id, Mission.status == "active"
    ).order_by(Mission.created_at.desc()))
    return [_out(db, m, user) for m in rows]


@router.post("/{mission_id}/run", response_model=MissionOut)
def rerun_mission(mission_id: uuid.UUID, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    m = db.get(Mission, mission_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mission not found")
    if _runs_today(m) >= settings.mission_daily_runs:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"這個任務今天跑過 {settings.mission_daily_runs} 次了，明天再試")
    _run(db, m, user)
    return _out(db, m, user)


@router.delete("/{mission_id}")
def archive_mission(mission_id: uuid.UUID, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    m = db.get(Mission, mission_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mission not found")
    m.status = "archived"
    db.commit()
    return {"archived": str(mission_id)}
