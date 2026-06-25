"""Load quest content from content/scenarios.yaml into the scenarios table.
Idempotent: upserts by `key`, so editing the YAML and re-running just updates.
This is the content pipeline — authors edit YAML, this loads it (no code change)."""

from pathlib import Path

import yaml

from app.core.db import SessionLocal
from app.models.dispatch import Scenario

CONTENT = Path(__file__).resolve().parent.parent / "content" / "scenarios.yaml"


def load(db, path: Path = CONTENT) -> int:
    if not path.exists():
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    count = 0
    for s in data.get("scenarios", []):
        key = s["key"]
        row = db.query(Scenario).filter(Scenario.key == key).one_or_none()
        fields = dict(
            title=s["title"],
            type=s.get("type", "solo"),
            art=s.get("art"),
            requirements=s.get("requirements", {}),
            rewards=s.get("rewards", {}),
            text_templates=s.get("text", {}),
            active=s.get("active", True),
        )
        if row is None:
            db.add(Scenario(key=key, **fields))
        else:
            for k, v in fields.items():
                setattr(row, k, v)
        count += 1
    db.commit()
    return count


def main() -> None:
    with SessionLocal() as db:
        n = load(db)
    print(f"load_scenarios: upserted {n} scenarios.")


if __name__ == "__main__":
    main()
