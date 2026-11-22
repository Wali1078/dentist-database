"""
Database connection and table initialisation.
DB path resolution: Windows -> Documents/Darya/clinic.db
                    Linux/Mac (dev) -> <project>/data/clinic.db
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Path resolution ────────────────────────────────────────────────────────
def _resolve_db_path() -> Path:
    custom = os.environ.get("DARYA_DB_PATH")
    if custom:
        p = Path(custom)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    if sys.platform == "win32":
        docs = Path.home() / "Documents"
        folder = docs / "Darya"
    else:
        # dev / Linux container
        folder = Path(__file__).parent.parent / "data"

    folder.mkdir(parents=True, exist_ok=True)
    return folder / "clinic.db"


DB_PATH = _resolve_db_path()
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Enable FK enforcement and WAL for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models import (  # noqa: F401 — imports trigger table registration
        patient, staff, appointment, dental_chart, invoice, inventory, expense
    )
    Base.metadata.create_all(bind=engine)
