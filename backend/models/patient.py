from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id                  = Column(Integer, primary_key=True, index=True)
    full_name           = Column(String(200), nullable=False)
    father_name         = Column(String(200))
    gender              = Column(String(10))          # مرد / زن / سایر
    date_of_birth       = Column(String(10))          # Shamsi YYYY-MM-DD
    phone               = Column(String(30))
    tazkira_number      = Column(String(50), nullable=True)
    province            = Column(String(100))
    district            = Column(String(100))
    address             = Column(Text)
    occupation          = Column(String(100))
    allergies           = Column(Text)
    chronic_conditions  = Column(Text)
    current_medications = Column(Text)
    notes               = Column(Text)
    is_archived         = Column(Boolean, default=False, nullable=False)
    created_at          = Column(String(20))
    updated_at          = Column(String(20))

    appointments   = relationship("Appointment",   back_populates="patient", lazy="dynamic")
    dental_records = relationship("DentalRecord",  back_populates="patient", lazy="dynamic")
    invoices       = relationship("Invoice",        back_populates="patient", lazy="dynamic")
