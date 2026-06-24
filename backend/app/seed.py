"""Idempotent catalog seed (axes, archetypes, scenarios) WITHOUT create_all.
Used on the migration path (prod) and by `make seed`. For dev you can still use
`python -m app.init_db` which also creates tables."""

from app.core.db import SessionLocal
from app.init_db import seed


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("seed: catalog ensured.")


if __name__ == "__main__":
    main()
