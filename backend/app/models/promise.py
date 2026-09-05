from datetime import datetime
from sqlalchemy import Column, String, Float, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    mandate_attempt_id = Column(String, ForeignKey("mandate_attempts.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    promised_date = Column(Date, nullable=False, index=True)

    # Status: "open" | "kept" | "broken" | "escalated"
    status = Column(String, default="open", index=True)

    grace_nudge_sent = Column(Boolean, default=False)
    payment_link_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="promises")
    mandate_attempt = relationship("MandateAttempt", back_populates="promises")
    conversations = relationship("ConversationLog", back_populates="promise", cascade="all, delete-orphan")


class ConversationLog(Base):
    __tablename__ = "conversation_log"

    id = Column(String, primary_key=True, index=True)
    promise_id = Column(String, ForeignKey("promises_to_pay.id"), nullable=False, index=True)
    sender = Column(String, nullable=False)  # "agent" | "customer"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    promise = relationship("PromiseToPay", back_populates="conversations")
