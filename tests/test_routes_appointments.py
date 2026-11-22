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


@pytest.fixture
def base_data(client):
    patient = client.post("/api/patients", json={"full_name": "بیمار نوبت"}).json()
    dentist = client.post("/api/staff", json={"full_name": "دکتر نوبت", "role": "دندانپزشک"}).json()
    return patient, dentist


def test_create_appointment(client, base_data):
    patient, dentist = base_data
    r = client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
        "appointment_time": "09:00",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "نوبت‌دار"
    assert data["appointment_date"] == "1403-01-15"


def test_list_appointments(client, base_data):
    patient, dentist = base_data
    client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })
    client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-16",
    })
    r = client.get("/api/appointments")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_by_date(client, base_data):
    patient, dentist = base_data
    client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })
    client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-20",
    })
    r = client.get("/api/appointments?date=1403-01-15")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_patch_status_valid(client, base_data):
    patient, dentist = base_data
    aid = client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    }).json()["id"]
    r = client.patch(f"/api/appointments/{aid}/status", json={"status": "تکمیل شده"})
    assert r.status_code == 200
    assert r.json()["status"] == "تکمیل شده"


def test_patch_status_invalid(client, base_data):
    patient, dentist = base_data
    aid = client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    }).json()["id"]
    r = client.patch(f"/api/appointments/{aid}/status", json={"status": "وضعیت_نامعتبر"})
    assert r.status_code == 422


def test_delete_appointment(client, base_data):
    patient, dentist = base_data
    aid = client.post("/api/appointments", json={
        "patient_id": patient["id"], "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    }).json()["id"]
    r = client.delete(f"/api/appointments/{aid}")
    assert r.status_code == 200
    assert client.get(f"/api/appointments/{aid}").status_code == 404


def test_appointment_invalid_patient(client, base_data):
    _, dentist = base_data
    r = client.post("/api/appointments", json={
        "patient_id": 9999, "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })
    assert r.status_code == 404
