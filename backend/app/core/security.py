"""Auth dependency. Production verifies a Supabase-signed JWT (HS256); dev mode
(no SUPABASE_JWT_SECRET) trusts an `X-Dev-User` header so the stack runs locally
without Supabase. The resolved principal is mapped to a local users row."""

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User


def _resolve_identity(authorization: str | None, x_dev_user: str | None) -> tuple[str, str | None]:
    """Return (supabase_uid_or_handle, email)."""
    if settings.supabase_jwt_secret:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
        token = authorization.split(" ", 1)[1]
        try:
            claims = jwt.decode(
                token, settings.supabase_jwt_secret,
                algorithms=["HS256"], audience="authenticated",
            )
        except jwt.PyJWTError as exc:  # pragma: no cover - thin wrapper
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}") from exc
        return claims["sub"], claims.get("email")

    # Dev fallback.
    if not x_dev_user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "dev mode: send X-Dev-User header (no SUPABASE_JWT_SECRET configured)",
        )
    return f"dev:{x_dev_user}", f"{x_dev_user}@dev.local"


def get_current_user(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    uid, email = _resolve_identity(authorization, x_dev_user)
    user = db.scalar(select(User).where(User.supabase_uid == uid))
    if user is None:
        # Just-in-time provisioning on first authenticated request.
        handle = uid.split(":", 1)[-1][:64]
        user = User(supabase_uid=uid, email=email, handle=handle, auth_provider="supabase")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
