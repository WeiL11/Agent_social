from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import CORE_AXIS_IDS
from app.models.catalog import Axis


def active_axis_ids(db: Session) -> list[str]:
    """Active radar axes from the registry; falls back to the core-8 constants if
    the table is empty (e.g. very first boot before seeding)."""
    ids = list(db.scalars(select(Axis.id).where(Axis.active.is_(True))))
    return ids or list(CORE_AXIS_IDS)
