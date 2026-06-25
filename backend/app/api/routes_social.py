"""Friends: send / accept / decline requests, list friends. A friendship is a
single row; direction is derived per viewer."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import Friendship
from app.models.user import User
from app.schemas.character import CharacterOut
from app.schemas.social import FriendOut, FriendRequestIn

router = APIRouter(prefix="/friends", tags=["friends"])


def _existing(db: Session, a: uuid.UUID, b: uuid.UUID) -> Friendship | None:
    return db.scalar(
        select(Friendship).where(
            or_(
                (Friendship.requester_id == a) & (Friendship.addressee_id == b),
                (Friendship.requester_id == b) & (Friendship.addressee_id == a),
            )
        )
    )


def _accepted_count(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(Friendship).where(
            Friendship.status == "accepted",
            or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
        )
    ) or 0


def _are_owner_friends(db: Session, a: uuid.UUID, b: uuid.UUID) -> bool:
    fr = _existing(db, a, b)
    return fr is not None and fr.status == "accepted"


@router.post("/requests", response_model=FriendOut)
def send_request(body: FriendRequestIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    target = db.scalar(select(User).where(User.handle == body.handle))
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot friend yourself")
    if _existing(db, user.id, target.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "request already exists")
    if _accepted_count(db, user.id) >= settings.owner_friend_cap:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"owner friend limit reached ({settings.owner_friend_cap})")
    fr = Friendship(requester_id=user.id, addressee_id=target.id, status="pending")
    db.add(fr)
    db.commit()
    db.refresh(fr)
    return FriendOut(friendship_id=fr.id, user_id=target.id, handle=target.handle,
                     status=fr.status, direction="outgoing")


@router.get("", response_model=list[FriendOut])
def list_friends(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Friendship).where(
            or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id)
        )
    )
    out: list[FriendOut] = []
    for fr in rows:
        other_id = fr.addressee_id if fr.requester_id == user.id else fr.requester_id
        other = db.get(User, other_id)
        if other is None:
            continue
        if fr.status == "accepted":
            direction = "friends"
        elif fr.requester_id == user.id:
            direction = "outgoing"
        else:
            direction = "incoming"
        out.append(FriendOut(friendship_id=fr.id, user_id=other_id, handle=other.handle,
                             status=fr.status, direction=direction))
    return out


@router.post("/requests/{friendship_id}/accept", response_model=FriendOut)
def accept_request(friendship_id: uuid.UUID, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    fr = db.get(Friendship, friendship_id)
    if fr is None or fr.addressee_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
    cap = settings.owner_friend_cap
    if _accepted_count(db, user.id) >= cap or _accepted_count(db, fr.requester_id) >= cap:
        raise HTTPException(status.HTTP_409_CONFLICT, f"owner friend limit reached ({cap})")
    fr.status = "accepted"
    db.commit()
    other = db.get(User, fr.requester_id)
    return FriendOut(friendship_id=fr.id, user_id=fr.requester_id,
                     handle=other.handle if other else "", status="accepted", direction="friends")


@router.delete("/requests/{friendship_id}")
def remove_or_decline(friendship_id: uuid.UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    fr = db.get(Friendship, friendship_id)
    if fr is None or user.id not in (fr.requester_id, fr.addressee_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    db.delete(fr)
    db.commit()
    return {"deleted": str(friendship_id)}


@router.get("/{friend_user_id}/characters", response_model=list[CharacterOut])
def friend_characters(friend_user_id: uuid.UUID, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """Owner-friend perk: see all characters a friend manages (their roster)."""
    if not _are_owner_friends(db, user.id, friend_user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not an accepted friend")
    rows = db.scalars(
        select(Character).where(Character.owner_id == friend_user_id).order_by(Character.slot)
    )
    return [CharacterOut.model_validate(c) for c in rows]
