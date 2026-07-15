from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# prepare_threshold=None disables psycopg named prepared statements — required
# with Supavisor/PgBouncer transaction pooling (shared server conns collide).
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True,
                       connect_args={"prepare_threshold": None})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
