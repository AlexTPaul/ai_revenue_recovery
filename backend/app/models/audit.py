from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)  # "mandate_attempt" | "promise_to_pay"
    entity_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Action: "retry_scheduled" | "retry_executed" | "nudge_sent" | "grace_nudge_sent" | "escalated" | "recovered"
    action = Column(String, nullable=False, index=True)

    reasoning = Column(Text, nullable=False)

    # Outcome: "pending" | "success" | "failure" | "escalated"
    outcome = Column(String, nullable=False)

    amount_recovered = Column(Float, nullable=True)
