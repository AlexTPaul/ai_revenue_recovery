from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MandateAttempt(Base):
    __tablename__ = "mandate_attempts"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    attempt_number = Column(Integer, default=1)
    scheduled_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    # Status: "pending" | "success" | "failed"
    status = Column(String, default="pending", index=True)

    # Failure Reason: "insufficient_funds" | "mandate_expired" | "bank_timeout" | "account_closed" | "technical_decline"
    failure_reason = Column(String, nullable=True, index=True)

    decision_explanation = Column(Text, nullable=True)

    # Next Action: "retry_scheduled" | "route_to_ptp" | "give_up" | "escalate"
    next_action = Column(String, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="attempts")
    promises = relationship("PromiseToPay", back_populates="mandate_attempt", cascade="all, delete-orphan")
