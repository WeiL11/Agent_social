"""Pytest fixtures. Unit tests need no DB. API tests use TEST_DATABASE_URL
(a Postgres URL); if it's unset they're skipped so `pytest` stays green locally
for pure-logic tests. CI sets TEST_DATABASE_URL to run the full suite."""

import os

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def client():
    if not TEST_DB:
        pytest.skip("TEST_DATABASE_URL not set; skipping DB-backed API tests")

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.db import get_db
    from app.init_db import seed
    from app.main import app
    from app.models import Base

    engine = create_engine(TEST_DB)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSession() as db:
        seed(db)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def auth(user: str = "alice") -> dict:
    return {"X-Dev-User": user}
