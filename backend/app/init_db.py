"""Dev convenience: create tables + seed the data-driven catalog. For production
use Alembic migrations instead (this stays idempotent and safe to re-run)."""

from sqlalchemy import select

from app.core.constants import ARCHETYPES, CORE_AXES, DEFAULT_AXIS_VALUE
from app.core.db import SessionLocal, engine
from app.models import Base  # noqa: F401  (ensures all models are registered)
from app.models.catalog import Archetype, Axis
from app.models.dispatch import Scenario


def seed(db) -> None:
    for a in CORE_AXES:
        if db.get(Axis, a["id"]) is None:
            db.add(Axis(id=a["id"], name=a["name"], category=a["category"],
                        active=True, default_value=DEFAULT_AXIS_VALUE))

    for a in ARCHETYPES:
        if db.get(Archetype, a["id"]) is None:
            db.add(Archetype(id=a["id"], name=a["name"],
                             default_species=a["default_species"], bias=a["bias"]))

    if db.scalar(select(Scenario).limit(1)) is None:
        db.add(Scenario(
            title="圖書館的謎題",
            type="solo",
            requirements={"min": {"logic": 55, "knowledge": 50}, "fail_above": {"humor": 95}},
            rewards={"xp": 100},
            text_templates={
                "success": "{name} 抽絲剝繭，解開了古老的索引謎題。",
                "fail": "{name} 被滿牆的書名繞暈了。",
            },
        ))
        db.add(Scenario(
            title="社區園遊會",
            type="solo",
            requirements={"min": {"empathy": 55, "humor": 50}},
            rewards={"xp": 100},
            text_templates={
                "success": "{name} 用笑容和耐心擺平了所有突發狀況。",
                "fail": "{name} 在人群裡有點手足無措。",
            },
        ))
    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    print("init_db: tables created and catalog seeded.")


if __name__ == "__main__":
    main()
