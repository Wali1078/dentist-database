from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"),     nullable=False)
    appointment_id   = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    invoice_date     = Column(String(10), nullable=False)       # Shamsi
    total_amount     = Column(Numeric(12, 2), nullable=False, default=0)   # before discount
    discount_amount  = Column(Numeric(12, 2), default=0)
    discount_reason  = Column(String(200))
    net_amount       = Column(Numeric(12, 2), nullable=False, default=0)   # total − discount
    amount_paid      = Column(Numeric(12, 2), default=0)        # sum of payments (cached)
    balance_due      = Column(Numeric(12, 2), default=0)        # net − paid (cached)
    status           = Column(String(30), default="پرداخت نشده")
    # پرداخت نشده / قسمی / پرداخت شده
    is_void          = Column(Boolean, default=False)
    void_reason      = Column(String(200))
    notes            = Column(Text)
    created_at       = Column(String(20))
    updated_at       = Column(String(20))

    patient     = relationship("Patient",     back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoices")
    payments    = relationship("Payment",     back_populates="invoice",
                               cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id              = Column(Integer, primary_key=True, index=True)
    invoice_id      = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount          = Column(Numeric(12, 2), nullable=False)
    payment_date    = Column(String(10), nullable=False)         # Shamsi
    received_by     = Column(Integer, ForeignKey("staff.id"), nullable=True)
    note            = Column(Text)
    created_at      = Column(String(20))

    invoice             = relationship("Invoice", back_populates="payments")
    received_by_staff   = relationship("Staff",   back_populates="payments_received")
