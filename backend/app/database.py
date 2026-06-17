"""Database engine / session setup (SQLite + SQLAlchemy)."""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import Base

settings = get_settings()

engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False},  # allow use across background threads
    future=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_con, _record):  # noqa: ANN001
    """Enforce foreign keys (off by default in SQLite)."""
    cur = dbapi_con.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a request-scoped session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
