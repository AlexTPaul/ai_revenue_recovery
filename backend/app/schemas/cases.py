from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    action: str
    reasoning: str
    outcome: str
    amount_recovered: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CaseListItem(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    customer_phone: str
    amount: float
    attempt_number: int
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    status: str
    failure_reason: Optional[str] = None
    decision_explanation: Optional[str] = None
    next_action: Optional[str] = None
    salary_credit_day: int
    mandate_id: str
    active_promise_id: Optional[str] = None
    promise_status: Optional[str] = None
    promised_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class CaseDetailResponse(BaseModel):
    case: CaseListItem
    audit_trail: List[AuditLogEntry]
