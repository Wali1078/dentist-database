from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from backend.database import get_db
from backend.models.expense import Expense
from backend.models.inventory import InventoryItem
from backend.shamsi import today_shamsi

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

VALID_CATEGORIES = {"معاش", "کرایه", "برق", "مواد", "متفرقه"}


class ExpenseIn(BaseModel):
    category: str
    amount: float
    expense_date: Optional[str] = None
    description: Optional[str] = None
    staff_id: Optional[int] = None
    inventory_item_id: Optional[int] = None
    quantity_purchased: Optional[float] = None


@router.get("")
def list_expenses(
    category: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Expense)
    if category:
        q = q.filter(Expense.category == category)
    if from_date:
        q = q.filter(Expense.expense_date >= from_date)
    if to_date:
        q = q.filter(Expense.expense_date <= to_date)
    return q.order_by(Expense.expense_date.desc()).all()


@router.get("/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    e = db.get(Expense, expense_id)
    if not e:
        raise HTTPException(404, "مصرف پیدا نشد")
    return e


@router.post("", status_code=201)
def create_expense(data: ExpenseIn, db: Session = Depends(get_db)):
    if data.category not in VALID_CATEGORIES:
        raise HTTPException(422, f"کتگوری نامعتبر: {data.category}")

    now = today_shamsi()
    e = Expense(
        category=data.category,
        amount=Decimal(str(data.amount)),
        expense_date=data.expense_date or now,
        description=data.description,
        staff_id=data.staff_id,
        inventory_item_id=data.inventory_item_id,
        quantity_purchased=Decimal(str(data.quantity_purchased)) if data.quantity_purchased else None,
        created_at=now,
    )
    db.add(e)

    # مواد category + inventory reference → increment stock
    if data.category == "مواد" and data.inventory_item_id and data.quantity_purchased:
        item = db.get(InventoryItem, data.inventory_item_id)
        if not item:
            raise HTTPException(404, f"مواد انبار {data.inventory_item_id} پیدا نشد")
        item.quantity_in_stock = Decimal(str(float(item.quantity_in_stock) + data.quantity_purchased))
        item.updated_at = now

    db.commit()
    db.refresh(e)
    return e


@router.put("/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn, db: Session = Depends(get_db)):
    e = db.get(Expense, expense_id)
    if not e:
        raise HTTPException(404, "مصرف پیدا نشد")
    if data.category not in VALID_CATEGORIES:
        raise HTTPException(422, f"کتگوری نامعتبر: {data.category}")
    e.category = data.category
    e.amount = Decimal(str(data.amount))
    e.expense_date = data.expense_date or e.expense_date
    e.description = data.description
    e.staff_id = data.staff_id
    e.inventory_item_id = data.inventory_item_id
    e.quantity_purchased = Decimal(str(data.quantity_purchased)) if data.quantity_purchased else None
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    e = db.get(Expense, expense_id)
    if not e:
        raise HTTPException(404, "مصرف پیدا نشد")
    db.delete(e)
    db.commit()
    return {"message": "مصرف حذف شد"}
