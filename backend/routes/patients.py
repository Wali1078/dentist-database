from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from pydantic import BaseModel
from backend.database import get_db
from backend.models.patient import Patient
from backend.models.appointment import Appointment
from backend.models.dental_chart import DentalRecord
from backend.models.invoice import Invoice
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientIn(BaseModel):
    full_name: str
    father_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    tazkira_number: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_patients(
    search: Optional[str] = Query(None),
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Patient)
    if not include_archived:
        q = q.filter(Patient.is_archived == False)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Patient.full_name.ilike(like))
            | (Patient.phone.ilike(like))
            | (Patient.tazkira_number.ilike(like))
        )
    return q.order_by(Patient.full_name).all()


@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "بیمار پیدا نشد")
    return p


@router.post("", status_code=201)
def create_patient(data: PatientIn, db: Session = Depends(get_db)):
    now = today_shamsi()
    p = Patient(**data.model_dump(), created_at=now, updated_at=now)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{patient_id}")
def update_patient(patient_id: int, data: PatientIn, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "بیمار پیدا نشد")
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    p.updated_at = today_shamsi()
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "بیمار پیدا نشد")
    has_history = (
        db.query(Appointment).filter(Appointment.patient_id == patient_id).first()
        or db.query(DentalRecord).filter(DentalRecord.patient_id == patient_id).first()
        or db.query(Invoice).filter(Invoice.patient_id == patient_id).first()
    )
    if has_history:
        p.is_archived = True
        p.updated_at = today_shamsi()
        db.commit()
        return {"action": "archived", "message": "بیمار به آرشیو منتقل شد"}
    db.delete(p)
    db.commit()
    return {"action": "deleted", "message": "بیمار حذف شد"}
