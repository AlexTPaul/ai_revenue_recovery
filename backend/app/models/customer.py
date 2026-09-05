from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    salary_credit_day = Column(Integer, nullable=False)  # 1 - 28
    mandate_id = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attempts = relationship("MandateAttempt", back_populates="customer", cascade="all, delete-orphan")
    promises = relationship("PromiseToPay", back_populates="customer", cascade="all, delete-orphan")
