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


def test_create_expense(client):
    r = client.post("/api/expenses", json={
        "category": "کرایه",
        "amount": 5000,
        "expense_date": "1403-01-01",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["category"] == "کرایه"
    assert float(data["amount"]) == 5000


def test_invalid_category(client):
    r = client.post("/api/expenses", json={
        "category": "نامعتبر",
        "amount": 1000,
    })
    assert r.status_code == 422


def test_expense_mawad_increments_stock(client):
    item = client.post("/api/inventory", json={
        "item_name": "گلاس آیونومر",
        "quantity_in_stock": 10,
        "reorder_level": 2,
        "cost_per_unit": 200,
    }).json()

    r = client.post("/api/expenses", json={
        "category": "مواد",
        "amount": 2000,
        "expense_date": "1403-01-05",
        "inventory_item_id": item["id"],
        "quantity_purchased": 5,
    })
    assert r.status_code == 201

    updated = client.get(f"/api/inventory/{item['id']}").json()
    assert float(updated["quantity_in_stock"]) == 15


def test_list_expenses(client):
    client.post("/api/expenses", json={"category": "برق", "amount": 1000})
    client.post("/api/expenses", json={"category": "معاش", "amount": 10000})
    r = client.get("/api/expenses")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_by_category(client):
    client.post("/api/expenses", json={"category": "برق", "amount": 1000})
    client.post("/api/expenses", json={"category": "معاش", "amount": 10000})
    r = client.get("/api/expenses?category=برق")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_delete_expense(client):
    eid = client.post("/api/expenses", json={"category": "متفرقه", "amount": 500}).json()["id"]
    r = client.delete(f"/api/expenses/{eid}")
    assert r.status_code == 200
    assert client.get(f"/api/expenses/{eid}").status_code == 404
