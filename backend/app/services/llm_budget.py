"""Daily LLM-call budget guard. Counter lives in the game_config KV table, so it
survives restarts and is shared by all callers. When the budget is exhausted,
callers fall back to the free template/rules engines — the game never breaks."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.admin import GameConfig


def _key() -> str:
    return "gemini_usage_" + datetime.now(UTC).strftime("%Y-%m-%d")


def try_spend_llm(db: Session, n: int = 1) -> bool:
    """Reserve n LLM calls from today's budget. Returns False when exhausted."""
    if not settings.gemini_api_key:
        return False
    row = db.get(GameConfig, _key())
    used = int((row.value or {}).get("count", 0)) if row else 0
    if used + n > settings.gemini_daily_budget:
        return False
    if row is None:
        db.add(GameConfig(key=_key(), value={"count": n}))
    else:
        row.value = {"count": used + n}
    db.commit()
    return True
