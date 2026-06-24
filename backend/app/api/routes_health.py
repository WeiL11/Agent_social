from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {"service": "ai-persona-game", "status": "ok", "env": settings.environment}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # pragma: no cover
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
