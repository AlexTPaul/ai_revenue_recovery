from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class EscalationQueueItem(BaseModel):
    case_id: str
    customer_id: str
    customer_name: str
    customer_phone: str
    amount: float
    failure_reason: str
    escalation_reason: str
    escalated_at: datetime
    status: str
    attempt_count: int


class ResolveEscalationRequest(BaseModel):
    resolution_notes: str
    action_taken: str  # e.g., "manual_payment_received", "mandate_cancelled", "written_off"
    amount_collected: Optional[float] = 0.0
