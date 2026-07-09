"""Current-user settings: discoverability opt-in/out and handle selection
(first-login onboarding for real-auth users)."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.matchmaking import MeOut, MeUpdate

router = APIRouter(prefix="/me", tags=["me"])

_HANDLE_RE = re.compile(r"^[a-z0-9_-]{3,24}$")


def _placeholder(u: User) -> bool:
    return u.handle.startswith("user-")


def _out(u: User) -> MeOut:
    return MeOut(handle=u.handle, discoverable=u.discoverable,
                 handle_is_placeholder=_placeholder(u))


@router.get("", response_model=MeOut)
def get_me(user: User = Depends(get_current_user)):
    return _out(user)


@router.put("", response_model=MeOut)
def update_me(body: MeUpdate, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    if body.handle is not None:
        handle = body.handle.strip().lower()
        if not _HANDLE_RE.match(handle):
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "handle must be 3-24 chars of a-z 0-9 _ -")
        if handle.startswith("user-"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "that prefix is reserved")
        taken = db.scalar(select(User).where(User.handle == handle, User.id != user.id))
        if taken is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "handle already taken")
        user.handle = handle
    if body.discoverable is not None:
        user.discoverable = body.discoverable
    db.commit()
    db.refresh(user)
    return _out(user)
