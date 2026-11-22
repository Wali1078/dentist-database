from sqlalchemy import Column, Integer, String, Boolean, Numeric
from sqlalchemy.orm import relationship
from backend.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id                   = Column(Integer, primary_key=True, index=True)
    full_name            = Column(String(200), nullable=False)
    role                 = Column(String(50), nullable=False)   # دندانپزشک/دستیار/پذیرش/خدمات
    specialization       = Column(String(100))
    license_number       = Column(String(50))
    phone                = Column(String(30))
    monthly_salary       = Column(Numeric(12, 2), default=0)    # AFN
    working_days         = Column(String(50))                   # e.g. "شنبه,یکشنبه"
    working_hours_start  = Column(String(5))                    # HH:MM
    working_hours_end    = Column(String(5))
    is_active            = Column(Boolean, default=True, nullable=False)
    hire_date            = Column(String(10))                   # Shamsi
    created_at           = Column(String(20))
    updated_at           = Column(String(20))

    appointments         = relationship("Appointment", back_populates="dentist", lazy="dynamic")
    payments_received    = relationship("Payment",     back_populates="received_by_staff", lazy="dynamic")
    expenses             = relationship("Expense",     back_populates="staff",   lazy="dynamic")
    dental_records       = relationship("DentalRecord", back_populates="dentist", lazy="dynamic")
