"""Dev convenience: create tables + seed the data-driven catalog. For production
use Alembic migrations instead (this stays idempotent and safe to re-run)."""

from app.core.constants import ARCHETYPES, CORE_AXES, DEFAULT_AXIS_VALUE
from app.core.db import SessionLocal, engine
from app.load_scenarios import load as load_scenarios
from app.models import Base  # noqa: F401  (ensures all models are registered)
from app.models.catalog import Archetype, Axis


def seed(db) -> None:
    for a in CORE_AXES:
        if db.get(Axis, a["id"]) is None:
            db.add(Axis(id=a["id"], name=a["name"], category=a["category"],
                        active=True, default_value=DEFAULT_AXIS_VALUE))

    for a in ARCHETYPES:
        if db.get(Archetype, a["id"]) is None:
            db.add(Archetype(id=a["id"], name=a["name"],
                             default_species=a["default_species"], bias=a["bias"]))
    db.commit()

    # Quest content comes from content/scenarios.yaml (idempotent upsert by key).
    load_scenarios(db)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    print("init_db: tables created and catalog seeded.")


if __name__ == "__main__":
    main()
