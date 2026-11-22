"""
End-to-end integration tests that chain operations across multiple modules.
These test realistic clinic workflows, not individual route correctness.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import backend.models
from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

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


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def dentist(client):
    r = client.post("/api/staff", json={"full_name": "دکتر احمدی", "role": "دندانپزشک"})
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def patient(client):
    r = client.post("/api/patients", json={
        "full_name": "فریده رحیمی",
        "phone": "0700123456",
        "gender": "زن",
        "date_of_birth": "1370-05-20",
        "province": "کابل",
    })
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def inventory_item(client):
    r = client.post("/api/inventory", json={
        "item_name": "کامپوزیت A2",
        "quantity_in_stock": 20,
        "reorder_level": 5,
        "cost_per_unit": 150,
        "unit_type": "گرام",
    })
    assert r.status_code == 201
    return r.json()


# ── Test: Full patient visit workflow ─────────────────────────────────────────

def test_full_patient_visit_workflow(client, patient, dentist, inventory_item):
    """
    Realistic clinic workflow:
    1. Create appointment
    2. Mark appointment تکمیل شده
    3. Create dental record with material usage → inventory decremented
    4. Create invoice
    5. Partial payment → status قسمی
    6. Final payment → status پرداخت شده
    7. Verify reports reflect the data
    """
    pid = patient["id"]
    did = dentist["id"]
    item_id = inventory_item["id"]

    # Step 1: Book appointment
    appt = client.post("/api/appointments", json={
        "patient_id": pid,
        "dentist_id": did,
        "appointment_date": "1403-06-15",
        "appointment_time": "10:00",
        "chief_complaint": "دندان درد",
    }).json()
    assert appt["status"] == "نوبت‌دار"

    # Step 2: Mark appointment complete
    r = client.patch(f"/api/appointments/{appt['id']}/status", json={"status": "تکمیل شده"})
    assert r.status_code == 200
    assert r.json()["status"] == "تکمیل شده"

    # Step 3: Add dental record with material — inventory must decrement
    stock_before = float(client.get(f"/api/inventory/{item_id}").json()["quantity_in_stock"])
    record = client.post("/api/dental/records", json={
        "patient_id": pid,
        "dentist_id": did,
        "tooth_number": 16,
        "condition": "پوسیدگی عمیق",
        "treatment_performed": "پر کردن کامپوزیت",
        "treatment_status": "تکمیل شده",
        "materials": [{"inventory_item_id": item_id, "quantity_used": 3}],
    }).json()
    assert record["tooth_number"] == 16
    stock_after = float(client.get(f"/api/inventory/{item_id}").json()["quantity_in_stock"])
    assert stock_after == stock_before - 3

    # Step 4: Create invoice
    invoice = client.post("/api/billing", json={
        "patient_id": pid,
        "total_amount": 3000,
        "discount_amount": 300,
        "discount_reason": "تخفیف بیمار قدیمی",
    }).json()
    assert float(invoice["net_amount"]) == 2700
    assert float(invoice["balance_due"]) == 2700
    assert invoice["status"] == "پرداخت نشده"

    inv_id = invoice["id"]

    # Step 5: Partial payment
    r = client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 1000})
    assert r.status_code == 201
    data = r.json()
    assert data["invoice_status"] == "قسمی"
    assert float(data["balance_due"]) == 1700

    # Step 6: Final payment
    r = client.post("/api/billing/payments", json={"invoice_id": inv_id, "amount": 1700})
    assert r.status_code == 201
    data = r.json()
    assert data["invoice_status"] == "پرداخت شده"
    assert float(data["balance_due"]) == 0

    # Verify payments list
    payments = client.get(f"/api/billing/{inv_id}/payments").json()
    assert len(payments) == 2
    total_paid = sum(float(p["amount"]) for p in payments)
    assert total_paid == 2700

    # Step 7: Check chart reflects the record
    chart = client.get(f"/api/dental/chart/{pid}").json()
    tooth16 = next((t for t in chart if t["tooth_number"] == 16), None)
    assert tooth16 is not None
    assert len(tooth16["history"]) == 1

    # Step 7b: Dashboard shows the patient
    dash = client.get("/api/reports/dashboard").json()
    assert dash["total_patients"] == 1


def test_expense_mawad_then_dental_decrements(client, patient, dentist):
    """
    مواد expense increments stock → dental record decrements it.
    Net result verified.
    """
    item = client.post("/api/inventory", json={
        "item_name": "گلاس آیونومر",
        "quantity_in_stock": 5,
        "reorder_level": 2,
        "cost_per_unit": 200,
    }).json()
    item_id = item["id"]

    # Purchase 10 units via expense
    client.post("/api/expenses", json={
        "category": "مواد",
        "amount": 2000,
        "expense_date": "1403-01-01",
        "inventory_item_id": item_id,
        "quantity_purchased": 10,
    })
    stock = float(client.get(f"/api/inventory/{item_id}").json()["quantity_in_stock"])
    assert stock == 15  # 5 + 10

    # Use 4 units in treatment
    client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 21,
        "materials": [{"inventory_item_id": item_id, "quantity_used": 4}],
    })
    stock = float(client.get(f"/api/inventory/{item_id}").json()["quantity_in_stock"])
    assert stock == 11  # 15 - 4


def test_staff_deactivated_not_in_dentist_list(client):
    """
    Deactivating a dentist removes them from the active dentist list.
    """
    dentist = client.post("/api/staff", json={"full_name": "دکتر غیر فعال", "role": "دندانپزشک"}).json()
    patient = client.post("/api/patients", json={"full_name": "بیمار الف"}).json()

    # Give dentist an appointment so deactivation (not deletion) triggers
    client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "appointment_date": "1403-01-15",
    })

    before = client.get("/api/staff/dentists").json()
    assert any(d["id"] == dentist["id"] for d in before)

    # Deactivate
    r = client.delete(f"/api/staff/{dentist['id']}")
    assert r.json()["action"] == "deactivated"

    # Should NOT appear in dentist list
    after = client.get("/api/staff/dentists").json()
    assert not any(d["id"] == dentist["id"] for d in after)


def test_patient_soft_delete_when_has_history(client, patient, dentist):
    """
    Patient with dental records must be archived (soft-delete), not hard-deleted.
    """
    pid = patient["id"]
    # Create a dental record
    client.post("/api/dental/records", json={
        "patient_id": pid,
        "dentist_id": dentist["id"],
        "tooth_number": 11,
        "condition": "پوسیدگی",
    })
    # Delete should archive
    r = client.delete(f"/api/patients/{pid}")
    assert r.status_code == 200
    body = r.json()
    # Either archived or action=archived
    assert body.get("is_archived") or body.get("action") == "archived"

    # Patient still accessible via direct get
    r2 = client.get(f"/api/patients/{pid}")
    assert r2.status_code == 200

    # But excluded from default list
    all_patients = client.get("/api/patients").json()
    assert not any(p["id"] == pid for p in all_patients)


def test_reports_monthly_aggregation(client, patient, dentist):
    """
    Monthly report correctly aggregates revenue and expenses for a given month.
    """
    # Create invoice and payments dated 1403-06
    inv = client.post("/api/billing", json={
        "patient_id": patient["id"],
        "total_amount": 5000,
        "invoice_date": "1403-06-10",
    }).json()
    client.post("/api/billing/payments", json={
        "invoice_id": inv["id"],
        "amount": 3000,
        "payment_date": "1403-06-10",
    })
    client.post("/api/billing/payments", json={
        "invoice_id": inv["id"],
        "amount": 2000,
        "payment_date": "1403-06-15",
    })

    # Create expense in same month
    client.post("/api/expenses", json={
        "category": "برق",
        "amount": 1500,
        "expense_date": "1403-06-05",
    })

    report = client.get("/api/reports/monthly?year=1403&month=6").json()
    assert float(report["revenue"]) == 5000
    assert float(report["expenses"]) == 1500
    assert float(report["profit"]) == 3500
    assert report["year"] == 1403
    assert report["month"] == 6


def test_low_stock_alert_after_treatment(client, patient, dentist):
    """
    After treatment uses up materials, low-stock endpoint should flag the item.
    """
    item = client.post("/api/inventory", json={
        "item_name": "بی‌حس کننده",
        "quantity_in_stock": 6,
        "reorder_level": 5,
        "cost_per_unit": 500,
    }).json()

    # Not low-stock yet (6 > 5)
    low = client.get("/api/inventory/low-stock").json()
    assert not any(i["id"] == item["id"] for i in low)

    # Use 2 units → stock becomes 4 ≤ reorder_level 5
    client.post("/api/dental/records", json={
        "patient_id": patient["id"],
        "dentist_id": dentist["id"],
        "tooth_number": 36,
        "materials": [{"inventory_item_id": item["id"], "quantity_used": 2}],
    })

    low = client.get("/api/inventory/low-stock").json()
    assert any(i["id"] == item["id"] for i in low)


def test_void_invoice_not_counted_in_revenue(client, patient):
    """
    Voided invoices should not contribute to revenue reports.
    """
    inv = client.post("/api/billing", json={
        "patient_id": patient["id"],
        "total_amount": 2000,
    }).json()

    # Void it (no payments, so allowed)
    client.patch(f"/api/billing/{inv['id']}/void", json={"void_reason": "اشتباه وارد شد"})

    report = client.get("/api/reports/revenue").json()
    assert float(report["total_revenue"]) == 0


def test_multiple_patients_multiple_invoices(client, dentist):
    """
    Multiple patients, invoices and payments — verify reports aggregate correctly.
    """
    p1 = client.post("/api/patients", json={"full_name": "بیمار الف"}).json()
    p2 = client.post("/api/patients", json={"full_name": "بیمار ب"}).json()
    p3 = client.post("/api/patients", json={"full_name": "بیمار ج"}).json()

    for pid, amount in [(p1["id"], 1000), (p2["id"], 2000), (p3["id"], 3000)]:
        inv = client.post("/api/billing", json={"patient_id": pid, "total_amount": amount}).json()
        client.post("/api/billing/payments", json={"invoice_id": inv["id"], "amount": amount})

    dash = client.get("/api/reports/dashboard").json()
    assert dash["total_patients"] == 3

    revenue = client.get("/api/reports/revenue").json()
    assert float(revenue["total_revenue"]) == 6000
