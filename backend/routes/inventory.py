from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from backend.database import get_db
from backend.models.inventory import InventoryItem
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class ItemIn(BaseModel):
    item_name: str
    category: Optional[str] = None
    unit_type: str = "عدد"
    quantity_in_stock: float = 0
    reorder_level: float = 5
    cost_per_unit: float = 0
    supplier_name: Optional[str] = None
    supplier_phone: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_items(
    low_stock: bool = False,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(InventoryItem)
    if category:
        q = q.filter(InventoryItem.category == category)
    if low_stock:
        q = q.filter(InventoryItem.quantity_in_stock <= InventoryItem.reorder_level)
    return q.order_by(InventoryItem.category, InventoryItem.item_name).all()


@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db)):
    return db.query(InventoryItem).filter(
        InventoryItem.quantity_in_stock <= InventoryItem.reorder_level
    ).order_by(InventoryItem.quantity_in_stock).all()


@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "مواد پیدا نشد")
    return item


@router.post("", status_code=201)
def create_item(data: ItemIn, db: Session = Depends(get_db)):
    now = today_shamsi()
    item = InventoryItem(
        **{k: Decimal(str(v)) if k in ("quantity_in_stock", "reorder_level", "cost_per_unit") else v
           for k, v in data.model_dump().items()},
        created_at=now, updated_at=now,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}")
def update_item(item_id: int, data: ItemIn, db: Session = Depends(get_db)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "مواد پیدا نشد")
    for k, v in data.model_dump().items():
        if k in ("quantity_in_stock", "reorder_level", "cost_per_unit"):
            setattr(item, k, Decimal(str(v)))
        else:
            setattr(item, k, v)
    item.updated_at = today_shamsi()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "مواد پیدا نشد")
    db.delete(item)
    db.commit()
    return {"message": "مواد حذف شد"}
