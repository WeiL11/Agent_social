"""Current-user settings, incl. matchmaking discoverability opt-in/out."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.matchmaking import MeOut, MeUpdate

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
def get_me(user: User = Depends(get_current_user)):
    return MeOut(handle=user.handle, discoverable=user.discoverable)


@router.put("", response_model=MeOut)
def update_me(body: MeUpdate, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    user.discoverable = body.discoverable
    db.commit()
    db.refresh(user)
    return MeOut(handle=user.handle, discoverable=user.discoverable)
