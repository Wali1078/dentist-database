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
    patient = client.post("/api/patients", json={"full_name": "بیمار دندان"}).json()
    dentist = client.post("/api/staff", json={"full_name": "دکتر دندان", "role": "دندانپزشک"}).json()
    return patient, dentist


def _make_record(client, patient_id, dentist_id, tooth=11):
    return client.post("/api/dental/records", json={
        "patient_id": patient_id,
        "dentist_id": dentist_id,
        "tooth_number": tooth,
        "condition": "پوسیدگی",
        "treatment_performed": "پر کردن",
        "treatment_status": "تکمیل شده",
    })


def test_create_record(client, base_data):
    patient, dentist = base_data
    r = _make_record(client, patient["id"], dentist["id"], tooth=11)
    assert r.status_code == 201
    data = r.json()
    assert data["tooth_number"] == 11
    assert data["condition"] == "پوسیدگی"


def test_invalid_tooth_number(client, base_data):
    patient, dentist = base_data
    r = client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 99,
    })
    assert r.status_code == 422


def test_child_tooth_valid(client, base_data):
    patient, dentist = base_data
    r = client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 51,
        "condition": "پوسیدگی",
    })
    assert r.status_code == 201


def test_get_chart(client, base_data):
    patient, dentist = base_data
    _make_record(client, patient["id"], dentist["id"], tooth=11)
    _make_record(client, patient["id"], dentist["id"], tooth=21)
    _make_record(client, patient["id"], dentist["id"], tooth=11)  # second record for tooth 11
    r = client.get(f"/api/dental/chart/{patient['id']}")
    assert r.status_code == 200
    chart = r.json()
    teeth = {t["tooth_number"] for t in chart}
    assert 11 in teeth
    assert 21 in teeth
    # tooth 11 should have 2 history entries
    tooth11 = next(t for t in chart if t["tooth_number"] == 11)
    assert len(tooth11["history"]) == 2


def test_inventory_decrement_on_record(client, base_data):
    patient, dentist = base_data
    item = client.post("/api/inventory", json={
        "item_name": "کامپوزیت",
        "quantity_in_stock": 10,
        "reorder_level": 2,
        "cost_per_unit": 100,
    }).json()

    r = client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 11,
        "condition": "پوسیدگی",
        "materials": [{"inventory_item_id": item["id"], "quantity_used": 3}],
    })
    assert r.status_code == 201
    updated = client.get(f"/api/inventory/{item['id']}").json()
    assert float(updated["quantity_in_stock"]) == 7


def test_insufficient_stock_rollback(client, base_data):
    patient, dentist = base_data
    item = client.post("/api/inventory", json={
        "item_name": "مواد کم",
        "quantity_in_stock": 1,
        "reorder_level": 0,
        "cost_per_unit": 100,
    }).json()

    r = client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 11,
        "materials": [{"inventory_item_id": item["id"], "quantity_used": 5}],
    })
    assert r.status_code == 400
    # Stock should be unchanged
    unchanged = client.get(f"/api/inventory/{item['id']}").json()
    assert float(unchanged["quantity_in_stock"]) == 1


def test_delete_record(client, base_data):
    patient, dentist = base_data
    rid = _make_record(client, patient["id"], dentist["id"]).json()["id"]
    r = client.delete(f"/api/dental/records/{rid}")
    assert r.status_code == 200
    assert client.get(f"/api/dental/records/{rid}").status_code == 404
