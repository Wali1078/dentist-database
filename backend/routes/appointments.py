from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from backend.database import get_db
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.staff import Staff
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


class AppointmentIn(BaseModel):
    patient_id: int
    dentist_id: int
    appointment_date: str
    appointment_time: Optional[str] = None
    visit_type: Optional[str] = "اولین ویزیت"
    chief_complaint: Optional[str] = None
    status: Optional[str] = "نوبت‌دار"
    next_appointment_note: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


@router.get("")
def list_appointments(
    date: Optional[str] = Query(None),
    week_start: Optional[str] = Query(None),
    dentist_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Appointment)
    if date:
        q = q.filter(Appointment.appointment_date == date)
    if week_start:
        # week_start is Shamsi YYYY-MM-DD; return 7 days from that date
        # We store dates as strings in YYYY-MM-DD so lexicographic compare works
        from backend.shamsi import shamsi_to_gregorian
        import datetime
        g_start = shamsi_to_gregorian(week_start)
        g_end   = g_start + datetime.timedelta(days=7)
        from backend.shamsi import gregorian_to_shamsi
        s_end = gregorian_to_shamsi(g_end)
        q = q.filter(
            Appointment.appointment_date >= week_start,
            Appointment.appointment_date < s_end,
        )
    if dentist_id:
        q = q.filter(Appointment.dentist_id == dentist_id)
    if patient_id:
        q = q.filter(Appointment.patient_id == patient_id)
    if status:
        q = q.filter(Appointment.status == status)
    return q.order_by(Appointment.appointment_date, Appointment.appointment_time).all()


@router.get("/today")
def today_appointments(db: Session = Depends(get_db)):
    today = today_shamsi()
    return db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).order_by(Appointment.appointment_time).all()


@router.get("/{appt_id}")
def get_appointment(appt_id: int, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "نوبت پیدا نشد")
    return a


@router.post("", status_code=201)
def create_appointment(data: AppointmentIn, db: Session = Depends(get_db)):
    if not db.get(Patient, data.patient_id):
        raise HTTPException(404, "بیمار پیدا نشد")
    if not db.get(Staff, data.dentist_id):
        raise HTTPException(404, "دندانپزشک پیدا نشد")
    now = today_shamsi()
    a = Appointment(**data.model_dump(), created_at=now, updated_at=now)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.put("/{appt_id}")
def update_appointment(appt_id: int, data: AppointmentIn, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "نوبت پیدا نشد")
    for k, v in data.model_dump().items():
        setattr(a, k, v)
    a.updated_at = today_shamsi()
    db.commit()
    db.refresh(a)
    return a


@router.patch("/{appt_id}/status")
def update_status(appt_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "نوبت پیدا نشد")
    valid = {"نوبت‌دار", "تکمیل شده", "لغو شده", "غایب"}
    if body.status not in valid:
        raise HTTPException(422, f"وضعیت نامعتبر: {body.status}")
    a.status = body.status
    a.updated_at = today_shamsi()
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{appt_id}")
def delete_appointment(appt_id: int, db: Session = Depends(get_db)):
    a = db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "نوبت پیدا نشد")
    db.delete(a)
    db.commit()
    return {"message": "نوبت حذف شد"}
