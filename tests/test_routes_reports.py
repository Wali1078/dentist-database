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


def test_dashboard_empty(client):
    r = client.get("/api/reports/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "today_appointments" in data
    assert "total_patients" in data
    assert data["today_appointments"] == 0
    assert data["total_patients"] == 0


def test_dashboard_with_data(client):
    patient = client.post("/api/patients", json={"full_name": "بیمار گزارش"}).json()
    dentist = client.post("/api/staff", json={"full_name": "دکتر گزارش", "role": "دندانپزشک"}).json()
    # We can't easily control "today" in tests; just verify structure
    r = client.get("/api/reports/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_patients"] == 1


def test_revenue_report(client):
    r = client.get("/api/reports/revenue")
    assert r.status_code == 200
    data = r.json()
    assert "total_revenue" in data
    assert data["total_revenue"] == 0


def test_expenses_summary_empty(client):
    r = client.get("/api/reports/expenses-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["by_category"] == {}


def test_expenses_summary_with_data(client):
    client.post("/api/expenses", json={"category": "برق", "amount": 1000, "expense_date": "1403-01-01"})
    client.post("/api/expenses", json={"category": "برق", "amount": 500, "expense_date": "1403-01-02"})
    client.post("/api/expenses", json={"category": "کرایه", "amount": 3000, "expense_date": "1403-01-03"})
    r = client.get("/api/reports/expenses-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["by_category"]["برق"] == 1500
    assert data["by_category"]["کرایه"] == 3000
    assert data["total"] == 4500


def test_monthly_report(client):
    r = client.get("/api/reports/monthly?year=1403&month=1")
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 1403
    assert data["month"] == 1
    assert "revenue" in data
    assert "expenses" in data
    assert "profit" in data


def test_patients_summary(client):
    client.post("/api/patients", json={"full_name": "بیمار الف", "gender": "مرد"})
    client.post("/api/patients", json={"full_name": "بیمار ب", "gender": "زن"})
    r = client.get("/api/reports/patients-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_active"] == 2
    assert data["total_archived"] == 0
