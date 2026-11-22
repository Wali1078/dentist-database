from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from backend.database import Base


class DentalRecord(Base):
    """One row per tooth per treatment visit."""
    __tablename__ = "dental_records"

    id                   = Column(Integer, primary_key=True, index=True)
    patient_id           = Column(Integer, ForeignKey("patients.id"),     nullable=False)
    appointment_id       = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    dentist_id           = Column(Integer, ForeignKey("staff.id"),        nullable=False)
    # FDI tooth number: 11-18, 21-28, 31-38, 41-48 (adult) / 51-55, 61-65, 71-75, 81-85 (child)
    tooth_number         = Column(Integer, nullable=False)
    tooth_surface        = Column(String(100))   # Mesial,Distal,Occlusal,Buccal,Lingual (comma-sep)
    condition            = Column(String(50))
    # پوسیدگی/شکستگی/آبسه/افتاده/نهفته/سالم/نیاز به روکش/نیاز به روت کانال
    treatment_performed  = Column(String(100))
    # پر کردن/کشیدن/روت کانال/روکش/بریج/پاک‌کاری/سفید کردن/ایمپلانت
    treatment_status     = Column(String(30), default="پلان شده")
    # پلان شده/در جریان/تکمیل شده
    treatment_date       = Column(String(10))    # Shamsi YYYY-MM-DD
    notes                = Column(Text)
    created_at           = Column(String(20))
    updated_at           = Column(String(20))

    patient     = relationship("Patient",     back_populates="dental_records")
    appointment = relationship("Appointment", back_populates="dental_records")
    dentist     = relationship("Staff",       back_populates="dental_records")
    materials   = relationship("TreatmentMaterial", back_populates="dental_record",
                               cascade="all, delete-orphan")


class TreatmentMaterial(Base):
    """Materials used in a dental procedure — decrements inventory on insert."""
    __tablename__ = "treatment_materials"

    id                = Column(Integer, primary_key=True, index=True)
    dental_record_id  = Column(Integer, ForeignKey("dental_records.id", ondelete="CASCADE"),
                               nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    quantity_used     = Column(Numeric(10, 3), nullable=False)
    created_at        = Column(String(20))

    dental_record  = relationship("DentalRecord",  back_populates="materials")
    inventory_item = relationship("InventoryItem", back_populates="usages")
