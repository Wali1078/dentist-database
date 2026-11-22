from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from backend.database import get_db
from backend.models.staff import Staff
from backend.models.appointment import Appointment
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/staff", tags=["staff"])


class StaffIn(BaseModel):
    full_name: str
    role: str
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    monthly_salary: Optional[float] = 0
    working_days: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    hire_date: Optional[str] = None


@router.get("")
def list_staff(
    role: Optional[str] = Query(None),
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(Staff)
    if active_only:
        q = q.filter(Staff.is_active == True)
    if role:
        q = q.filter(Staff.role == role)
    return q.order_by(Staff.full_name).all()


@router.get("/dentists")
def list_dentists(db: Session = Depends(get_db)):
    return db.query(Staff).filter(
        Staff.role == "دندانپزشک", Staff.is_active == True
    ).order_by(Staff.full_name).all()


@router.get("/{staff_id}")
def get_staff(staff_id: int, db: Session = Depends(get_db)):
    s = db.get(Staff, staff_id)
    if not s:
        raise HTTPException(404, "کارمند پیدا نشد")
    return s


@router.get("/{staff_id}/stats")
def staff_stats(staff_id: int, db: Session = Depends(get_db)):
    s = db.get(Staff, staff_id)
    if not s:
        raise HTTPException(404, "کارمند پیدا نشد")
    total_appts = db.query(func.count(Appointment.id)).filter(
        Appointment.dentist_id == staff_id
    ).scalar() or 0
    unique_patients = db.query(func.count(Appointment.patient_id.distinct())).filter(
        Appointment.dentist_id == staff_id
    ).scalar() or 0
    return {
        "staff_id": staff_id,
        "full_name": s.full_name,
        "total_appointments": total_appts,
        "unique_patients": unique_patients,
    }


@router.post("", status_code=201)
def create_staff(data: StaffIn, db: Session = Depends(get_db)):
    now = today_shamsi()
    s = Staff(**data.model_dump(), created_at=now, updated_at=now)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/{staff_id}")
def update_staff(staff_id: int, data: StaffIn, db: Session = Depends(get_db)):
    s = db.get(Staff, staff_id)
    if not s:
        raise HTTPException(404, "کارمند پیدا نشد")
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    s.updated_at = today_shamsi()
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{staff_id}")
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
    s = db.get(Staff, staff_id)
    if not s:
        raise HTTPException(404, "کارمند پیدا نشد")
    has_appointments = db.query(Appointment).filter(
        Appointment.dentist_id == staff_id
    ).first()
    if has_appointments:
        s.is_active = False
        s.updated_at = today_shamsi()
        db.commit()
        return {"action": "deactivated", "message": "کارمند غیرفعال شد"}
    db.delete(s)
    db.commit()
    return {"action": "deleted", "message": "کارمند حذف شد"}
