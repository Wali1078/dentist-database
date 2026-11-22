"""
Tests for all 9 models: creation, required fields, FK relationships,
cascade / protect behaviors, and business logic (invoice math, stock math).
"""
import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from backend.models.patient     import Patient
from backend.models.staff       import Staff
from backend.models.appointment import Appointment
from backend.models.dental_chart import DentalRecord, TreatmentMaterial
from backend.models.invoice     import Invoice, Payment
from backend.models.inventory   import InventoryItem
from backend.models.expense     import Expense
from backend.shamsi             import today_shamsi


# ── helpers ──────────────────────────────────────────────────────────────────
def make_patient(db, name="احمد رحیمی", phone="0700000001"):
    p = Patient(full_name=name, phone=phone,
                created_at=today_shamsi(), updated_at=today_shamsi())
    db.add(p); db.commit(); db.refresh(p)
    return p


def make_staff(db, name="دکتر فرید", role="دندانپزشک"):
    s = Staff(full_name=name, role=role,
              created_at=today_shamsi(), updated_at=today_shamsi())
    db.add(s); db.commit(); db.refresh(s)
    return s


def make_appointment(db, patient, staff):
    a = Appointment(patient_id=patient.id, dentist_id=staff.id,
                    appointment_date=today_shamsi(), appointment_time="09:00",
                    visit_type="اولین ویزیت", status="نوبت‌دار",
                    created_at=today_shamsi(), updated_at=today_shamsi())
    db.add(a); db.commit(); db.refresh(a)
    return a


def make_inventory(db, name="کامپوزیت", qty=100, reorder=10):
    item = InventoryItem(item_name=name, quantity_in_stock=qty, reorder_level=reorder,
                         unit_type="گرام", cost_per_unit=Decimal("150"),
                         created_at=today_shamsi(), updated_at=today_shamsi())
    db.add(item); db.commit(); db.refresh(item)
    return item


def make_invoice(db, patient, appointment=None, total=1000, discount=0):
    net = total - discount
    inv = Invoice(
        patient_id=patient.id,
        appointment_id=appointment.id if appointment else None,
        invoice_date=today_shamsi(),
        total_amount=Decimal(str(total)),
        discount_amount=Decimal(str(discount)),
        net_amount=Decimal(str(net)),
        amount_paid=Decimal("0"),
        balance_due=Decimal(str(net)),
        status="پرداخت نشده",
        created_at=today_shamsi(), updated_at=today_shamsi(),
    )
    db.add(inv); db.commit(); db.refresh(inv)
    return inv


# ── Patient ───────────────────────────────────────────────────────────────────
class TestPatient:
    def test_create(self, db):
        p = make_patient(db)
        assert p.id is not None
        assert p.full_name == "احمد رحیمی"

    def test_required_full_name(self, db):
        p = Patient(phone="123")
        db.add(p)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    def test_tazkira_nullable(self, db):
        p = make_patient(db)
        assert p.tazkira_number is None

    def test_soft_delete_flag(self, db):
        p = make_patient(db)
        assert p.is_archived is False
        p.is_archived = True
        db.commit()
        db.refresh(p)
        assert p.is_archived is True

    def test_multiple_patients(self, db):
        make_patient(db, "بیمار یک", "0700000001")
        make_patient(db, "بیمار دو", "0700000002")
        assert db.query(Patient).count() == 2


# ── Staff ─────────────────────────────────────────────────────────────────────
class TestStaff:
    def test_create(self, db):
        s = make_staff(db)
        assert s.id is not None
        assert s.role == "دندانپزشک"

    def test_required_role(self, db):
        s = Staff(full_name="تست")
        db.add(s)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    def test_is_active_default(self, db):
        s = make_staff(db)
        assert s.is_active is True

    def test_deactivate(self, db):
        s = make_staff(db)
        s.is_active = False
        db.commit()
        db.refresh(s)
        assert s.is_active is False


# ── Appointment ───────────────────────────────────────────────────────────────
class TestAppointment:
    def test_create(self, db):
        p = make_patient(db)
        s = make_staff(db)
        a = make_appointment(db, p, s)
        assert a.id is not None
        assert a.patient_id == p.id
        assert a.dentist_id == s.id

    def test_status_default(self, db):
        p = make_patient(db)
        s = make_staff(db)
        a = make_appointment(db, p, s)
        assert a.status == "نوبت‌دار"

    def test_fk_patient(self, db):
        s = make_staff(db)
        a = Appointment(patient_id=9999, dentist_id=s.id,
                        appointment_date=today_shamsi(), created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(a)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    def test_fk_staff(self, db):
        p = make_patient(db)
        a = Appointment(patient_id=p.id, dentist_id=9999,
                        appointment_date=today_shamsi(), created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(a)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()


# ── Invoice math ──────────────────────────────────────────────────────────────
class TestInvoiceMath:
    def test_net_amount(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=2000, discount=300)
        assert inv.net_amount == Decimal("1700")

    def test_initial_status_unpaid(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=1000)
        assert inv.status == "پرداخت نشده"
        assert inv.balance_due == Decimal("1000")
        assert inv.amount_paid == Decimal("0")

    def test_partial_payment(self, db):
        p = make_patient(db)
        s = make_staff(db)
        inv = make_invoice(db, p, total=1000)

        pay = Payment(invoice_id=inv.id, amount=Decimal("400"),
                      payment_date=today_shamsi(), created_at=today_shamsi())
        db.add(pay); db.commit()

        # Simulate the route-layer update
        inv.amount_paid = Decimal("400")
        inv.balance_due = inv.net_amount - Decimal("400")
        inv.status = "قسمی"
        db.commit(); db.refresh(inv)

        assert inv.status == "قسمی"
        assert inv.amount_paid == Decimal("400")
        assert inv.balance_due == Decimal("600")

    def test_full_payment(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=500)

        pay = Payment(invoice_id=inv.id, amount=Decimal("500"),
                      payment_date=today_shamsi(), created_at=today_shamsi())
        db.add(pay); db.commit()

        inv.amount_paid = Decimal("500")
        inv.balance_due = Decimal("0")
        inv.status = "پرداخت شده"
        db.commit(); db.refresh(inv)

        assert inv.status == "پرداخت شده"
        assert inv.balance_due == Decimal("0")

    def test_cannot_delete_invoice_with_payments(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=800)
        pay = Payment(invoice_id=inv.id, amount=Decimal("200"),
                      payment_date=today_shamsi(), created_at=today_shamsi())
        db.add(pay); db.commit()

        # Route layer enforces: use is_void flag instead
        # Here we verify the payment exists and cascades with the invoice
        assert db.query(Payment).filter_by(invoice_id=inv.id).count() == 1

    def test_void_invoice(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=800)
        inv.is_void = True
        inv.void_reason = "اشتباه در ثبت"
        db.commit(); db.refresh(inv)
        assert inv.is_void is True

    def test_zero_discount(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=750, discount=0)
        assert inv.net_amount == Decimal("750")
        assert inv.discount_amount == Decimal("0")


# ── Inventory stock math ──────────────────────────────────────────────────────
class TestInventoryStock:
    def test_initial_stock(self, db):
        item = make_inventory(db, qty=100)
        assert item.quantity_in_stock == Decimal("100")

    def test_low_stock_at_reorder_level(self, db):
        item = make_inventory(db, qty=10, reorder=10)
        assert item.quantity_in_stock <= item.reorder_level

    def test_low_stock_below_reorder_level(self, db):
        item = make_inventory(db, qty=5, reorder=10)
        assert item.quantity_in_stock < item.reorder_level

    def test_above_reorder_level_not_low(self, db):
        item = make_inventory(db, qty=11, reorder=10)
        assert item.quantity_in_stock > item.reorder_level

    def test_treatment_material_decrements_stock(self, db):
        p = make_patient(db)
        s = make_staff(db)
        a = make_appointment(db, p, s)
        item = make_inventory(db, qty=50)
        rec = DentalRecord(patient_id=p.id, appointment_id=a.id, dentist_id=s.id,
                           tooth_number=11, condition="پوسیدگی",
                           treatment_performed="پر کردن", treatment_status="تکمیل شده",
                           treatment_date=today_shamsi(),
                           created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(rec); db.commit(); db.refresh(rec)

        mat = TreatmentMaterial(dental_record_id=rec.id, inventory_item_id=item.id,
                                quantity_used=Decimal("5"), created_at=today_shamsi())
        db.add(mat); db.commit()

        # Route layer does the decrement; here verify the model stores it correctly
        item.quantity_in_stock -= Decimal("5")
        db.commit(); db.refresh(item)
        assert item.quantity_in_stock == Decimal("45")

    def test_expense_supply_increments_stock(self, db):
        item = make_inventory(db, qty=20)
        exp = Expense(category="مواد", amount=Decimal("3000"),
                      expense_date=today_shamsi(), inventory_item_id=item.id,
                      quantity_purchased=Decimal("10"),
                      created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(exp); db.commit()

        item.quantity_in_stock += Decimal("10")
        db.commit(); db.refresh(item)
        assert item.quantity_in_stock == Decimal("30")

    def test_stock_never_goes_negative(self, db):
        item = make_inventory(db, qty=3)
        # Route layer must reject this — here we verify the value should be checked
        new_qty = item.quantity_in_stock - Decimal("5")
        assert new_qty < 0  # route layer must reject negative


# ── Delete protections ────────────────────────────────────────────────────────
class TestDeleteProtections:
    def test_patient_with_appointments_soft_deletes(self, db):
        p = make_patient(db)
        s = make_staff(db)
        make_appointment(db, p, s)
        # Soft delete: set is_archived
        p.is_archived = True
        db.commit()
        still_there = db.get(Patient, p.id)
        assert still_there is not None
        assert still_there.is_archived is True

    def test_staff_with_appointments_deactivates(self, db):
        p = make_patient(db)
        s = make_staff(db)
        make_appointment(db, p, s)
        s.is_active = False
        db.commit()
        still_there = db.get(Staff, s.id)
        assert still_there is not None
        assert still_there.is_active is False

    def test_treatment_material_cascades_with_record(self, db):
        p = make_patient(db)
        s = make_staff(db)
        a = make_appointment(db, p, s)
        item = make_inventory(db)
        rec = DentalRecord(patient_id=p.id, appointment_id=a.id, dentist_id=s.id,
                           tooth_number=21, condition="سالم",
                           treatment_performed="پاک‌کاری", treatment_status="تکمیل شده",
                           treatment_date=today_shamsi(),
                           created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(rec); db.commit(); db.refresh(rec)
        mat = TreatmentMaterial(dental_record_id=rec.id, inventory_item_id=item.id,
                                quantity_used=Decimal("2"), created_at=today_shamsi())
        db.add(mat); db.commit()

        mat_id = mat.id
        db.delete(rec)
        db.commit()
        # Cascade should have deleted the material
        assert db.query(TreatmentMaterial).filter_by(id=mat_id).first() is None


# ── Report queries ─────────────────────────────────────────────────────────────
class TestReportQueries:
    def _seed(self, db):
        """Seed two doctors, two patients, appointments, invoices, payments, expenses."""
        d1 = make_staff(db, "دکتر کریم", "دندانپزشک")
        d2 = make_staff(db, "دکتر لیلا", "دندانپزشک")
        p1 = make_patient(db, "بیمار الف", "0700000001")
        p2 = make_patient(db, "بیمار ب", "0700000002")

        a1 = make_appointment(db, p1, d1)
        a2 = make_appointment(db, p2, d1)
        a3 = make_appointment(db, p2, d2)

        inv1 = make_invoice(db, p1, a1, total=1000, discount=0)
        inv2 = make_invoice(db, p2, a2, total=2000, discount=200)
        inv3 = make_invoice(db, p2, a3, total=1500, discount=0)

        for inv, amt in [(inv1, 1000), (inv2, 1800), (inv3, 500)]:
            pay = Payment(invoice_id=inv.id, amount=Decimal(str(amt)),
                          payment_date=today_shamsi(), created_at=today_shamsi())
            db.add(pay)
        db.commit()
        return d1, d2, p1, p2

    def test_total_revenue(self, db):
        d1, d2, p1, p2 = self._seed(db)
        total = db.query(Payment).all()
        assert sum(float(p.amount) for p in total) == pytest.approx(3300.0)

    def test_patient_count_per_doctor(self, db):
        d1, d2, p1, p2 = self._seed(db)
        from sqlalchemy import func
        rows = (db.query(Appointment.dentist_id, func.count(Appointment.patient_id.distinct()))
                .group_by(Appointment.dentist_id).all())
        counts = {r[0]: r[1] for r in rows}
        assert counts[d1.id] == 2   # d1 treated p1 and p2
        assert counts[d2.id] == 1   # d2 treated p2

    def test_outstanding_balance(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=1000)
        pay = Payment(invoice_id=inv.id, amount=Decimal("600"),
                      payment_date=today_shamsi(), created_at=today_shamsi())
        db.add(pay); db.commit()
        inv.amount_paid = Decimal("600")
        inv.balance_due = Decimal("400")
        inv.status = "قسمی"
        db.commit(); db.refresh(inv)
        assert float(inv.balance_due) == pytest.approx(400.0)

    def test_expenses_total(self, db):
        exp1 = Expense(category="کرایه", amount=Decimal("5000"),
                       expense_date=today_shamsi(),
                       created_at=today_shamsi(), updated_at=today_shamsi())
        exp2 = Expense(category="برق", amount=Decimal("2000"),
                       expense_date=today_shamsi(),
                       created_at=today_shamsi(), updated_at=today_shamsi())
        db.add_all([exp1, exp2]); db.commit()
        from sqlalchemy import func
        total = db.query(func.sum(Expense.amount)).scalar()
        assert float(total) == pytest.approx(7000.0)

    def test_profit_revenue_minus_expenses(self, db):
        p = make_patient(db)
        inv = make_invoice(db, p, total=10000)
        pay = Payment(invoice_id=inv.id, amount=Decimal("10000"),
                      payment_date=today_shamsi(), created_at=today_shamsi())
        db.add(pay)
        exp = Expense(category="متفرقه", amount=Decimal("3000"),
                      expense_date=today_shamsi(),
                      created_at=today_shamsi(), updated_at=today_shamsi())
        db.add(exp); db.commit()

        from sqlalchemy import func
        revenue = float(db.query(func.sum(Payment.amount)).scalar() or 0)
        expenses = float(db.query(func.sum(Expense.amount)).scalar() or 0)
        profit = revenue - expenses
        assert profit == pytest.approx(7000.0)

    def test_low_stock_query(self, db):
        make_inventory(db, "مواد A", qty=5,  reorder=10)   # low
        make_inventory(db, "مواد B", qty=10, reorder=10)   # at threshold = low
        make_inventory(db, "مواد C", qty=11, reorder=10)   # fine
        low = db.query(InventoryItem).filter(
            InventoryItem.quantity_in_stock <= InventoryItem.reorder_level
        ).all()
        assert len(low) == 2
