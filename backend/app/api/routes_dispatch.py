"""#3 dispatch: list scenarios, send characters on a task, get a deterministic
rule-resolved outcome + apply A-system growth on success."""

import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import active_axis_ids
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.dispatch import Dispatch, Scenario
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.dispatch import DispatchRequest, DispatchResult, ScenarioOut
from app.services.progression import apply_rewards
from app.services.resolver import resolve

router = APIRouter(tags=["dispatch"])

_SEED_MAX = 2_147_483_647


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.scalars(select(Scenario).where(Scenario.active.is_(True)))
    return [ScenarioOut.model_validate(s) for s in rows]


@router.post("/dispatches", response_model=DispatchResult)
def create_dispatch(body: DispatchRequest, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    scenario = db.get(Scenario, body.scenario_id)
    if scenario is None or not scenario.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "scenario not found")

    chars = [db.get(Character, cid) for cid in body.character_ids]
    if any(c is None or c.owner_id != user.id for c in chars):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")

    seed = body.seed if body.seed is not None else random.randint(1, _SEED_MAX)
    char_dicts = [{"name": c.name, "radar": c.radar, "trait_tags": c.trait_tags} for c in chars]
    result = resolve(
        char_dicts,
        {"requirements": scenario.requirements, "rewards": scenario.rewards,
         "text_templates": scenario.text_templates},
        seed,
        active_axis_ids(db),
    )

    if result["outcome"] == "success":
        for c in chars:
            apply_rewards(c, result["rewards"])

    dispatch = Dispatch(
        user_id=user.id, character_ids=[str(c.id) for c in chars],
        scenario_id=scenario.id, seed=seed, outcome=result["outcome"],
        log=result["log"], rewards_granted=result["rewards"],
    )
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    for c in chars:
        db.refresh(c)

    return DispatchResult(
        dispatch_id=dispatch.id, outcome=result["outcome"], log=result["log"],
        rewards=result["rewards"], characters=[CharacterOut.model_validate(c) for c in chars],
    )
