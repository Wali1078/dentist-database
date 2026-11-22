import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import backend.models  # register all ORM models with Base
from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def set_pragmas(conn, _):
        conn.cursor().execute("PRAGMA foreign_keys = ON")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def _make_item(client, name="کامپوزیت", qty=10, reorder=5):
    return client.post("/api/inventory", json={
        "item_name": name,
        "quantity_in_stock": qty,
        "reorder_level": reorder,
        "cost_per_unit": 100,
    })


def test_create_item(client):
    r = _make_item(client)
    assert r.status_code == 201
    data = r.json()
    assert data["item_name"] == "کامپوزیت"
    assert float(data["quantity_in_stock"]) == 10


def test_list_items(client):
    _make_item(client, "کامپوزیت")
    _make_item(client, "آمالگام")
    r = client.get("/api/inventory")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_low_stock_filter(client):
    _make_item(client, "کم موجود", qty=3, reorder=5)
    _make_item(client, "موجود کافی", qty=10, reorder=5)
    r = client.get("/api/inventory/low-stock")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["item_name"] == "کم موجود"


def test_update_item(client):
    item_id = _make_item(client).json()["id"]
    r = client.put(f"/api/inventory/{item_id}", json={
        "item_name": "کامپوزیت بروزشده",
        "quantity_in_stock": 20,
        "reorder_level": 5,
        "cost_per_unit": 150,
    })
    assert r.status_code == 200
    assert r.json()["item_name"] == "کامپوزیت بروزشده"
    assert float(r.json()["quantity_in_stock"]) == 20


def test_delete_item(client):
    item_id = _make_item(client).json()["id"]
    r = client.delete(f"/api/inventory/{item_id}")
    assert r.status_code == 200
    assert client.get(f"/api/inventory/{item_id}").status_code == 404


def test_get_item_not_found(client):
    assert client.get("/api/inventory/999").status_code == 404
