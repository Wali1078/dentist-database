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
def patient_id(client):
    return client.post("/api/patients", json={"full_name": "بیمار فاکتور"}).json()["id"]


def _make_invoice(client, patient_id, total=1000, discount=0):
    return client.post("/api/billing", json={
        "patient_id": patient_id,
        "total_amount": total,
        "discount_amount": discount,
    })


def test_create_invoice(client, patient_id):
    r = _make_invoice(client, patient_id, total=5000, discount=500)
    assert r.status_code == 201
    data = r.json()
    assert float(data["total_amount"]) == 5000
    assert float(data["net_amount"]) == 4500
    assert float(data["balance_due"]) == 4500
    assert data["status"] == "پرداخت نشده"


def test_add_payment_partial(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=2000).json()["id"]
    r = client.post("/api/billing/payments", json={
        "invoice_id": inv_id,
        "amount": 1000,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["invoice_status"] == "قسمی"
    assert float(data["balance_due"]) == 1000


def test_add_payment_full(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=1500).json()["id"]
    r = client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 1500})
    assert r.status_code == 201
    assert r.json()["invoice_status"] == "پرداخت شده"
    assert float(r.json()["balance_due"]) == 0


def test_overpayment_rejected(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=1000).json()["id"]
    r = client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 2000})
    assert r.status_code == 400


def test_void_invoice_no_payments(client, patient_id):
    inv_id = _make_invoice(client, patient_id).json()["id"]
    r = client.patch(f"/api/billing/{inv_id}/void", json={"void_reason": "اشتباه وارد شد"})
    assert r.status_code == 200


def test_cannot_void_invoice_with_payments(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=1000).json()["id"]
    client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 500})
    r = client.patch(f"/api/billing/{inv_id}/void", json={"void_reason": "تست"})
    assert r.status_code == 400


def test_delete_invoice_with_payments_blocked(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=1000).json()["id"]
    client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 500})
    r = client.delete(f"/api/billing/{inv_id}")
    assert r.status_code == 400


def test_delete_invoice_without_payments(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=1000).json()["id"]
    r = client.delete(f"/api/billing/{inv_id}")
    assert r.status_code == 200


def test_list_payments(client, patient_id):
    inv_id = _make_invoice(client, patient_id, total=3000).json()["id"]
    client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 1000})
    client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 2000})
    r = client.get(f"/api/billing/{inv_id}/payments")
    assert r.status_code == 200
    assert len(r.json()) == 2
