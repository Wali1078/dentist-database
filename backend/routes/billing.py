from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel
from backend.database import get_db
from backend.models.invoice import Invoice, Payment
from backend.models.patient import Patient
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/billing", tags=["billing"])


class InvoiceIn(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    invoice_date: Optional[str] = None
    total_amount: float
    discount_amount: float = 0
    discount_reason: Optional[str] = None
    notes: Optional[str] = None


class PaymentIn(BaseModel):
    invoice_id: int
    amount: float
    payment_date: Optional[str] = None
    received_by: Optional[int] = None
    note: Optional[str] = None


def _recalc_invoice(db: Session, invoice: Invoice):
    """Recalculate amount_paid, balance_due and status from payments table."""
    total_paid = db.query(func.sum(Payment.amount)).filter(
        Payment.invoice_id == invoice.id
    ).scalar() or Decimal("0")

    invoice.amount_paid = Decimal(str(total_paid))
    invoice.balance_due = invoice.net_amount - invoice.amount_paid

    if invoice.amount_paid >= invoice.net_amount:
        invoice.status = "پرداخت شده"
    elif invoice.amount_paid > 0:
        invoice.status = "قسمی"
    else:
        invoice.status = "پرداخت نشده"

    invoice.updated_at = today_shamsi()


@router.get("")
def list_invoices(
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Invoice).filter(Invoice.is_void == False)
    if patient_id:
        q = q.filter(Invoice.patient_id == patient_id)
    if status:
        q = q.filter(Invoice.status == status)
    return q.order_by(Invoice.invoice_date.desc()).all()


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    return inv


@router.post("", status_code=201)
def create_invoice(data: InvoiceIn, db: Session = Depends(get_db)):
    if not db.get(Patient, data.patient_id):
        raise HTTPException(404, "بیمار پیدا نشد")
    total = Decimal(str(data.total_amount))
    discount = Decimal(str(data.discount_amount))
    net = total - discount
    now = today_shamsi()
    inv = Invoice(
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        invoice_date=data.invoice_date or now,
        total_amount=total,
        discount_amount=discount,
        discount_reason=data.discount_reason,
        net_amount=net,
        amount_paid=Decimal("0"),
        balance_due=net,
        status="پرداخت نشده",
        notes=data.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.put("/{invoice_id}")
def update_invoice(invoice_id: int, data: InvoiceIn, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    if inv.is_void:
        raise HTTPException(400, "صورت‌حساب باطل شده قابل ویرایش نیست")
    total = Decimal(str(data.total_amount))
    discount = Decimal(str(data.discount_amount))
    inv.total_amount = total
    inv.discount_amount = discount
    inv.discount_reason = data.discount_reason
    inv.net_amount = total - discount
    inv.notes = data.notes
    _recalc_invoice(db, inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.patch("/{invoice_id}/void")
def void_invoice(invoice_id: int, body: dict, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    has_payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).first()
    if has_payments:
        raise HTTPException(400, "صورت‌حساب دارای پرداخت است و نمی‌توان حذف کرد")
    inv.is_void = True
    inv.void_reason = body.get("void_reason", "")
    inv.updated_at = today_shamsi()
    db.commit()
    return {"message": "صورت‌حساب باطل شد"}


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    has_payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).first()
    if has_payments:
        raise HTTPException(400, "صورت‌حساب دارای پرداخت است — برای ابطال از PATCH /void استفاده کنید")
    db.delete(inv)
    db.commit()
    return {"message": "صورت‌حساب حذف شد"}


# ── Payments ──────────────────────────────────────────────────────────────────

@router.get("/{invoice_id}/payments")
def list_payments(invoice_id: int, db: Session = Depends(get_db)):
    if not db.get(Invoice, invoice_id):
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    return db.query(Payment).filter(Payment.invoice_id == invoice_id).all()


@router.post("/payments", status_code=201)
def add_payment(data: PaymentIn, db: Session = Depends(get_db)):
    inv = db.get(Invoice, data.invoice_id)
    if not inv:
        raise HTTPException(404, "صورت‌حساب پیدا نشد")
    if inv.is_void:
        raise HTTPException(400, "صورت‌حساب باطل شده است")

    amount = Decimal(str(data.amount))
    if amount <= 0:
        raise HTTPException(422, "مبلغ پرداخت باید بیشتر از صفر باشد")

    # Reject overpayment
    remaining = inv.balance_due
    if amount > remaining:
        raise HTTPException(400, f"مبلغ پرداخت ({amount} ؋) بیشتر از مانده ({remaining} ؋) است")

    now = today_shamsi()
    pay = Payment(
        invoice_id=data.invoice_id,
        amount=amount,
        payment_date=data.payment_date or now,
        received_by=data.received_by,
        note=data.note,
        created_at=now,
    )
    db.add(pay)
    db.flush()
    _recalc_invoice(db, inv)
    db.commit()
    db.refresh(inv)
    return {"payment_id": pay.id, "invoice_status": inv.status, "balance_due": float(inv.balance_due)}
