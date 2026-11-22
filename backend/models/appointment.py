from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id                    = Column(Integer, primary_key=True, index=True)
    patient_id            = Column(Integer, ForeignKey("patients.id"), nullable=False)
    dentist_id            = Column(Integer, ForeignKey("staff.id"),    nullable=False)
    appointment_date      = Column(String(10), nullable=False)   # Shamsi YYYY-MM-DD
    appointment_time      = Column(String(5))                    # HH:MM
    visit_type            = Column(String(50))                   # اولین ویزیت/مراجعه دوباره/اورژانس
    chief_complaint       = Column(Text)
    status                = Column(String(30), default="نوبت‌دار")
    # نوبت‌دار / تکمیل شده / لغو شده / غایب
    next_appointment_note = Column(Text)
    created_at            = Column(String(20))
    updated_at            = Column(String(20))

    patient        = relationship("Patient",     back_populates="appointments")
    dentist        = relationship("Staff",       back_populates="appointments")
    dental_records = relationship("DentalRecord", back_populates="appointment", lazy="dynamic")
    invoices       = relationship("Invoice",      back_populates="appointment",  lazy="dynamic")
