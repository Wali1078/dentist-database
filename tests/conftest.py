"""Shared pytest fixtures — in-memory SQLite DB per test."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DARYA_DB_PATH"] = ":memory:"   # will be overridden per-session below

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import patient, staff, appointment, dental_chart, invoice, inventory, expense  # noqa


@pytest.fixture
def db():
    """Fresh in-memory SQLite session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_pragmas(conn, _):
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
