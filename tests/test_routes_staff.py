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


def _make_staff(client, name="دکتر علی", role="دندانپزشک"):
    return client.post("/api/staff", json={"full_name": name, "role": role})


def test_create_staff(client):
    r = _make_staff(client)
    assert r.status_code == 201
    data = r.json()
    assert data["full_name"] == "دکتر علی"
    assert data["is_active"] == True


def test_list_staff(client):
    _make_staff(client, "دکتر علی")
    _make_staff(client, "نرس فاطمه", "نرس")
    r = client.get("/api/staff")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_dentists(client):
    _make_staff(client, "دکتر علی", "دندانپزشک")
    _make_staff(client, "نرس فاطمه", "نرس")
    r = client.get("/api/staff/dentists")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["role"] == "دندانپزشک"


def test_get_staff_not_found(client):
    assert client.get("/api/staff/999").status_code == 404


def test_update_staff(client):
    sid = _make_staff(client).json()["id"]
    r = client.put(f"/api/staff/{sid}", json={"full_name": "دکتر احمد", "role": "دندانپزشک"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "دکتر احمد"


def test_delete_staff_no_appointments(client):
    sid = _make_staff(client).json()["id"]
    r = client.delete(f"/api/staff/{sid}")
    assert r.status_code == 200
    assert r.json()["action"] == "deleted"


def test_deactivate_staff_with_appointments(client):
    dentist = _make_staff(client, "دکتر محمد", "دندانپزشک").json()
    patient = client.post("/api/patients", json={"full_name": "بیمار تست"}).json()
    client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })
    r = client.delete(f"/api/staff/{dentist['id']}")
    assert r.status_code == 200
    assert r.json()["action"] == "deactivated"
    # Staff still exists but is inactive
    s = client.get(f"/api/staff/{dentist['id']}").json()
    assert s["is_active"] == False


def test_staff_stats(client):
    dentist = _make_staff(client, "دکتر آمار", "دندانپزشک").json()
    patient = client.post("/api/patients", json={"full_name": "بیمار آمار"}).json()
    client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })
    r = client.get(f"/api/staff/{dentist['id']}/stats")
    assert r.status_code == 200
    assert r.json()["total_appointments"] == 1
