"""Owner-friend direct messages. Gated to accepted owner-friends only."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.message import Message
from app.models.social import Friendship
from app.models.user import User
from app.schemas.message import ConversationOut, MessageIn, MessageOut

router = APIRouter(tags=["messages"])


def _require_friend(db: Session, me: uuid.UUID, other: uuid.UUID) -> None:
    fr = db.scalar(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                (Friendship.requester_id == me) & (Friendship.addressee_id == other),
                (Friendship.requester_id == other) & (Friendship.addressee_id == me),
            ),
        )
    )
    if fr is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "you can only message accepted friends")


@router.post("/friends/{friend_user_id}/messages", response_model=MessageOut)
def send_message(friend_user_id: uuid.UUID, body: MessageIn, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    if friend_user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot message yourself")
    _require_friend(db, user.id, friend_user_id)
    msg = Message(from_user_id=user.id, to_user_id=friend_user_id, body=body.body)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageOut(id=msg.id, from_me=True, body=msg.body, created_at=msg.created_at, read=False)


@router.get("/friends/{friend_user_id}/messages", response_model=list[MessageOut])
def get_messages(friend_user_id: uuid.UUID, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    _require_friend(db, user.id, friend_user_id)
    rows = list(db.scalars(
        select(Message).where(
            or_(
                (Message.from_user_id == user.id) & (Message.to_user_id == friend_user_id),
                (Message.from_user_id == friend_user_id) & (Message.to_user_id == user.id),
            )
        ).order_by(Message.created_at)
    ))
    # mark incoming as read
    now = datetime.now(UTC)
    for m in rows:
        if m.to_user_id == user.id and m.read_at is None:
            m.read_at = now
    db.commit()
    return [
        MessageOut(id=m.id, from_me=(m.from_user_id == user.id), body=m.body,
                   created_at=m.created_at, read=m.read_at is not None)
        for m in rows
    ]


@router.get("/conversations", response_model=list[ConversationOut])
def conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """One row per accepted friend with last message + unread count (for a chat list)."""
    friends = db.scalars(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id),
        )
    )
    out: list[ConversationOut] = []
    for fr in friends:
        other_id = fr.addressee_id if fr.requester_id == user.id else fr.requester_id
        other = db.get(User, other_id)
        if other is None:
            continue
        last = db.scalar(
            select(Message).where(
                or_(
                    (Message.from_user_id == user.id) & (Message.to_user_id == other_id),
                    (Message.from_user_id == other_id) & (Message.to_user_id == user.id),
                )
            ).order_by(Message.created_at.desc()).limit(1)
        )
        unread = db.scalar(
            select(func.count()).select_from(Message).where(
                and_(Message.from_user_id == other_id, Message.to_user_id == user.id,
                     Message.read_at.is_(None))
            )
        ) or 0
        out.append(ConversationOut(
            friend_user_id=other_id, handle=other.handle,
            last_message=last.body if last else None,
            last_at=last.created_at if last else None, unread=unread,
        ))
    out.sort(key=lambda c: c.last_at.timestamp() if c.last_at else 0.0, reverse=True)
    return out
