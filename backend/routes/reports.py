from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from backend.database import get_db
from backend.models.invoice import Invoice, Payment
from backend.models.appointment import Appointment
from backend.models.expense import Expense
from backend.models.patient import Patient
from backend.shamsi import today_shamsi, shamsi_year_month, gregorian_to_shamsi
import datetime

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = today_shamsi()

    today_appts = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date == today
    ).scalar() or 0

    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.is_archived == False
    ).scalar() or 0

    # Revenue this month
    year, month = shamsi_year_month(today)
    month_prefix = f"{year:04d}-{month:02d}"
    month_revenue = db.query(func.sum(Payment.amount)).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).filter(
        Invoice.is_void == False,
        Payment.payment_date.like(f"{month_prefix}%"),
    ).scalar() or Decimal("0")

    # Monthly expenses
    month_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.like(f"{month_prefix}%")
    ).scalar() or Decimal("0")

    # Unpaid invoices count
    unpaid = db.query(func.count(Invoice.id)).filter(
        Invoice.is_void == False,
        Invoice.status == "پرداخت نشده",
    ).scalar() or 0

    return {
        "today": today,
        "today_appointments": today_appts,
        "total_patients": total_patients,
        "month_revenue": float(month_revenue),
        "month_expenses": float(month_expenses),
        "month_profit": float(month_revenue) - float(month_expenses),
        "unpaid_invoices": unpaid,
    }


@router.get("/revenue")
def revenue_report(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    today = today_shamsi()
    q = db.query(Payment).join(Invoice, Payment.invoice_id == Invoice.id).filter(
        Invoice.is_void == False
    )
    if from_date:
        q = q.filter(Payment.payment_date >= from_date)
    if to_date:
        q = q.filter(Payment.payment_date <= to_date)

    payments = q.all()
    total = sum(float(p.amount) for p in payments)
    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_revenue": total,
        "payment_count": len(payments),
    }


@router.get("/expenses-summary")
def expenses_summary(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Expense.category, func.sum(Expense.amount).label("total")).group_by(Expense.category)
    if from_date:
        q = q.filter(Expense.expense_date >= from_date)
    if to_date:
        q = q.filter(Expense.expense_date <= to_date)
    rows = q.all()
    result = {row.category: float(row.total) for row in rows}
    grand_total = sum(result.values())
    return {"from_date": from_date, "to_date": to_date, "by_category": result, "total": grand_total}


@router.get("/monthly")
def monthly_report(year: int, month: int, db: Session = Depends(get_db)):
    prefix = f"{year:04d}-{month:02d}"

    revenue = db.query(func.sum(Payment.amount)).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).filter(
        Invoice.is_void == False,
        Payment.payment_date.like(f"{prefix}%"),
    ).scalar() or Decimal("0")

    expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.like(f"{prefix}%")
    ).scalar() or Decimal("0")

    appt_count = db.query(func.count(Appointment.id)).filter(
        Appointment.appointment_date.like(f"{prefix}%")
    ).scalar() or 0

    new_patients = db.query(func.count(Patient.id)).filter(
        Patient.created_at.like(f"{prefix}%")
    ).scalar() or 0

    return {
        "year": year,
        "month": month,
        "revenue": float(revenue),
        "expenses": float(expenses),
        "profit": float(revenue) - float(expenses),
        "appointments": appt_count,
        "new_patients": new_patients,
    }


@router.get("/patients-summary")
def patients_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Patient.id)).filter(Patient.is_archived == False).scalar() or 0
    archived = db.query(func.count(Patient.id)).filter(Patient.is_archived == True).scalar() or 0
    by_gender = db.query(Patient.gender, func.count(Patient.id)).filter(
        Patient.is_archived == False
    ).group_by(Patient.gender).all()
    return {
        "total_active": total,
        "total_archived": archived,
        "by_gender": {g or "نامشخص": c for g, c in by_gender},
    }
