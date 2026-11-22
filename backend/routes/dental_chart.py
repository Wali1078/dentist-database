from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel
from backend.database import get_db
from backend.models.dental_chart import DentalRecord, TreatmentMaterial
from backend.models.inventory import InventoryItem
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/dental", tags=["dental"])

VALID_TEETH_ADULT = set(range(11, 19)) | set(range(21, 29)) | set(range(31, 39)) | set(range(41, 49))
VALID_TEETH_CHILD = set(range(51, 56)) | set(range(61, 66)) | set(range(71, 76)) | set(range(81, 86))
VALID_TEETH = VALID_TEETH_ADULT | VALID_TEETH_CHILD


class MaterialIn(BaseModel):
    inventory_item_id: int
    quantity_used: float


class DentalRecordIn(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    dentist_id: int
    tooth_number: int
    tooth_surface: Optional[str] = None
    condition: Optional[str] = None
    treatment_performed: Optional[str] = None
    treatment_status: Optional[str] = "پلان شده"
    treatment_date: Optional[str] = None
    notes: Optional[str] = None
    materials: Optional[List[MaterialIn]] = []


@router.get("/records")
def list_records(
    patient_id: Optional[int] = Query(None),
    tooth_number: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(DentalRecord)
    if patient_id:
        q = q.filter(DentalRecord.patient_id == patient_id)
    if tooth_number:
        q = q.filter(DentalRecord.tooth_number == tooth_number)
    return q.order_by(DentalRecord.treatment_date.desc()).all()


@router.get("/chart/{patient_id}")
def get_chart(patient_id: int, db: Session = Depends(get_db)):
    """Return all teeth records for a patient grouped by tooth number."""
    records = db.query(DentalRecord).filter(
        DentalRecord.patient_id == patient_id
    ).order_by(DentalRecord.tooth_number, DentalRecord.treatment_date.desc()).all()

    chart = {}
    for rec in records:
        tn = rec.tooth_number
        if tn not in chart:
            chart[tn] = {"tooth_number": tn, "latest": None, "history": []}
        entry = {
            "id": rec.id,
            "condition": rec.condition,
            "treatment_performed": rec.treatment_performed,
            "treatment_status": rec.treatment_status,
            "treatment_date": rec.treatment_date,
            "notes": rec.notes,
            "dentist_id": rec.dentist_id,
        }
        if chart[tn]["latest"] is None:
            chart[tn]["latest"] = entry
        chart[tn]["history"].append(entry)

    return list(chart.values())


@router.get("/records/{record_id}")
def get_record(record_id: int, db: Session = Depends(get_db)):
    r = db.get(DentalRecord, record_id)
    if not r:
        raise HTTPException(404, "سابقه پیدا نشد")
    return r


@router.post("/records", status_code=201)
def create_record(data: DentalRecordIn, db: Session = Depends(get_db)):
    if data.tooth_number not in VALID_TEETH:
        raise HTTPException(422, f"شماره دندان نامعتبر: {data.tooth_number}")

    now = today_shamsi()
    payload = data.model_dump(exclude={"materials"})
    if not payload.get("treatment_date"):
        payload["treatment_date"] = now

    rec = DentalRecord(**payload, created_at=now, updated_at=now)
    db.add(rec)
    db.flush()  # get rec.id before adding materials

    for mat in (data.materials or []):
        item = db.get(InventoryItem, mat.inventory_item_id)
        if not item:
            db.rollback()
            raise HTTPException(404, f"مواد انبار {mat.inventory_item_id} پیدا نشد")
        new_qty = float(item.quantity_in_stock) - mat.quantity_used
        if new_qty < 0:
            db.rollback()
            raise HTTPException(400, f"موجودی کافی برای {item.item_name} وجود ندارد")
        item.quantity_in_stock = Decimal(str(new_qty))
        item.updated_at = now
        m = TreatmentMaterial(
            dental_record_id=rec.id,
            inventory_item_id=mat.inventory_item_id,
            quantity_used=Decimal(str(mat.quantity_used)),
            created_at=now,
        )
        db.add(m)

    db.commit()
    db.refresh(rec)
    return rec


@router.put("/records/{record_id}")
def update_record(record_id: int, data: DentalRecordIn, db: Session = Depends(get_db)):
    rec = db.get(DentalRecord, record_id)
    if not rec:
        raise HTTPException(404, "سابقه پیدا نشد")
    if data.tooth_number not in VALID_TEETH:
        raise HTTPException(422, f"شماره دندان نامعتبر: {data.tooth_number}")
    for k, v in data.model_dump(exclude={"materials"}).items():
        setattr(rec, k, v)
    rec.updated_at = today_shamsi()
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.get(DentalRecord, record_id)
    if not rec:
        raise HTTPException(404, "سابقه پیدا نشد")
    db.delete(rec)
    db.commit()
    return {"message": "سابقه حذف شد"}
