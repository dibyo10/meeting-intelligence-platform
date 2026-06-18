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


def recover_interrupted_meetings() -> int:
    """Mark meetings left mid-pipeline by a crash/restart as errored.

    The ingest pipeline runs in an in-process background task, so a server restart while a
    meeting is ``queued``/``processing`` would otherwise leave it stuck in that state
    forever. On startup we flip those to ``error`` so the UI shows a clear, reprocessable
    state instead of an endless spinner. Returns the number of rows fixed.
    """
    from .models import STATUS_ERROR, STATUS_PROCESSING, STATUS_QUEUED, Meeting

    db = SessionLocal()
    try:
        stuck = (
            db.query(Meeting)
            .filter(Meeting.status.in_([STATUS_QUEUED, STATUS_PROCESSING]))
            .all()
        )
        for m in stuck:
            m.status = STATUS_ERROR
            m.stage = "error"
            m.error = "Processing was interrupted by a server restart. Reprocess to retry."
        if stuck:
            db.commit()
        return len(stuck)
    finally:
        db.close()


def get_db():
    """FastAPI dependency that yields a request-scoped session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
