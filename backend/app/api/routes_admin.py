"""Admin/ops surface — deliberately separated from player routes under /admin
with its own role gate. MVP exposes the moderation queue; sqladmin / Supabase
Table Editor cover the rest of live-ops for now."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.admin import AdminUser, AuditLog, ModerationItem
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> User:
    admin = db.scalar(select(AdminUser).where(AdminUser.user_id == user.id))
    if admin is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


@router.get("/health")
def admin_health(user: User = Depends(require_admin)):
    return {"status": "ok", "admin": str(user.id)}


@router.get("/moderation")
def moderation_queue(status_filter: str = "pending", db: Session = Depends(get_db),
                     _: User = Depends(require_admin)):
    rows = db.scalars(
        select(ModerationItem).where(ModerationItem.status == status_filter).limit(100)
    )
    return [{"id": str(m.id), "kind": m.kind, "ref_id": m.ref_id,
             "payload": m.payload, "status": m.status} for m in rows]


@router.post("/moderation/{item_id}")
def resolve_moderation(item_id: uuid.UUID, decision: str, db: Session = Depends(get_db),
                       admin: User = Depends(require_admin)):
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "decision must be approved/rejected")
    item = db.get(ModerationItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "item not found")
    item.status = decision
    db.add(AuditLog(actor_id=admin.id, action="moderation.resolve",
                    target=str(item_id), detail={"decision": decision}))
    db.commit()
    return {"id": str(item_id), "status": decision}
