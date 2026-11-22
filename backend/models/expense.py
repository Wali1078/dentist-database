from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Expense(Base):
    """
    An expense row.
    - category=مواد + inventory_item_id → ALSO increments inventory.quantity_in_stock
      by quantity_purchased.  This logic lives in the route layer.
    - category=معاش + staff_id → salary payment for a staff member.
    """
    __tablename__ = "expenses"

    id                  = Column(Integer, primary_key=True, index=True)
    category            = Column(String(50), nullable=False)
    # معاش / کرایه / برق / مواد / متفرقه
    amount              = Column(Numeric(12, 2), nullable=False)       # AFN
    expense_date        = Column(String(10), nullable=False)           # Shamsi
    description         = Column(Text)
    staff_id            = Column(Integer, ForeignKey("staff.id"), nullable=True)
    inventory_item_id   = Column(Integer, ForeignKey("inventory.id"), nullable=True)
    quantity_purchased  = Column(Numeric(12, 3), nullable=True)
    created_at          = Column(String(20))
    updated_at          = Column(String(20))

    staff          = relationship("Staff",         back_populates="expenses")
    inventory_item = relationship("InventoryItem", back_populates="expenses")
