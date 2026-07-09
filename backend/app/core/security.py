"""Auth dependency. Three modes, checked in order:

1. Supabase asymmetric JWT (new projects): SUPABASE_PROJECT_URL set -> verify
   RS256/ES256 against the project's JWKS endpoint (cached client).
2. Supabase legacy JWT secret: SUPABASE_JWT_SECRET set -> verify HS256.
3. Dev fallback (local only, neither set): trust the X-Dev-User header.

The resolved principal is JIT-provisioned into the local users table. New users
get a placeholder handle (user-xxxxxxxx) and pick a real one via PUT /me."""

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User

_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = settings.supabase_project_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)
    return _jwks_client


def _decode_supabase(token: str) -> dict:
    try:
        if settings.supabase_project_url:
            key = _get_jwks_client().get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, algorithms=["ES256", "RS256"],
                              audience="authenticated")
        return jwt.decode(token, settings.supabase_jwt_secret,
                          algorithms=["HS256"], audience="authenticated")
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}") from exc


def _resolve_identity(authorization: str | None, x_dev_user: str | None) -> tuple[str, str | None]:
    """Return (stable_uid, email)."""
    if settings.supabase_project_url or settings.supabase_jwt_secret:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
        claims = _decode_supabase(authorization.split(" ", 1)[1])
        return claims["sub"], claims.get("email")

    # Dev fallback (no Supabase configured — local only).
    if not x_dev_user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "dev mode: send X-Dev-User header (no Supabase auth configured)",
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
        # JIT provisioning. Real-auth users get a placeholder handle and are
        # prompted by the frontend to choose one (PUT /me).
        if uid.startswith("dev:"):
            handle = uid.split(":", 1)[-1][:64]
        else:
            handle = f"user-{uid.replace('-', '')[:8]}"
        user = User(supabase_uid=uid, email=email, handle=handle, auth_provider="supabase")
        db.add(user)
        db.commit()
        db.refresh(user)
    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "account suspended")
    return user
