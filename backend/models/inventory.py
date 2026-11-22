from sqlalchemy import Column, Integer, String, Numeric, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory"

    id                = Column(Integer, primary_key=True, index=True)
    item_name         = Column(String(200), nullable=False)
    category          = Column(String(100))
    unit_type         = Column(String(20), default="عدد")     # ml/گرام/عدد/بسته
    quantity_in_stock = Column(Numeric(12, 3), default=0)
    reorder_level     = Column(Numeric(12, 3), default=5)
    cost_per_unit     = Column(Numeric(12, 2), default=0)     # AFN
    supplier_name     = Column(String(200))
    supplier_phone    = Column(String(30))
    expiry_date       = Column(String(10), nullable=True)     # Shamsi, nullable
    notes             = Column(Text)
    created_at        = Column(String(20))
    updated_at        = Column(String(20))

    usages   = relationship("TreatmentMaterial", back_populates="inventory_item", lazy="dynamic")
    expenses = relationship("Expense",           back_populates="inventory_item", lazy="dynamic")
