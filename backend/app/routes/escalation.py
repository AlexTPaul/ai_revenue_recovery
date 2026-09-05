import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.mandate import MandateAttempt
from app.models.promise import PromiseToPay
from app.models.audit import AuditLog
from app.schemas.escalation import EscalationQueueItem, ResolveEscalationRequest
from app.services.clock_service import clock_service

router = APIRouter(prefix="/escalation", tags=["Human Escalation Queue"])


@router.get("/queue", response_model=List[EscalationQueueItem])
def get_escalation_queue(db: Session = Depends(get_db)):
    """Retrieves all cases currently handed off to the Human Escalation Queue."""
    # Find all cases with audit log action 'escalated'
    escalated_logs = (
        db.query(AuditLog)
        .filter(AuditLog.action == "escalated")
        .order_by(desc(AuditLog.timestamp))
        .all()
    )

    items: List[EscalationQueueItem] = []
    seen_entity_ids = set()

    for log in escalated_logs:
        if log.entity_id in seen_entity_ids:
            continue
        seen_entity_ids.add(log.entity_id)

        # Check if entity is MandateAttempt or PromiseToPay
        if log.entity_type == "mandate_attempt":
            attempt = db.query(MandateAttempt).filter(MandateAttempt.id == log.entity_id).first()
            if attempt and attempt.customer:
                items.append(
                    EscalationQueueItem(
                        case_id=attempt.id,
                        customer_id=attempt.customer.id,
                        customer_name=attempt.customer.name,
                        customer_phone=attempt.customer.phone,
                        amount=attempt.amount,
                        failure_reason=attempt.failure_reason or "manual_escalation",
                        escalation_reason=log.reasoning,
                        escalated_at=log.timestamp,
                        status="pending_human_action",
                        attempt_count=attempt.attempt_number,
                    )
                )
        elif log.entity_type == "promise_to_pay":
            promise = db.query(PromiseToPay).filter(PromiseToPay.id == log.entity_id).first()
            if promise and promise.customer:
                items.append(
                    EscalationQueueItem(
                        case_id=promise.id,
                        customer_id=promise.customer.id,
                        customer_name=promise.customer.name,
                        customer_phone=promise.customer.phone,
                        amount=promise.amount,
                        failure_reason="broken_promise_grace_elapsed",
                        escalation_reason=log.reasoning,
                        escalated_at=log.timestamp,
                        status="pending_human_action",
                        attempt_count=3,
                    )
                )

    return items


@router.post("/{case_id}/resolve")
def resolve_escalated_case(
    case_id: str,
    payload: ResolveEscalationRequest,
    db: Session = Depends(get_db),
):
    """Allows support personnel to mark an escalated case as resolved or closed."""
    current_time = clock_service.get_current_time(db)

    audit = AuditLog(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        entity_type="escalation_resolution",
        entity_id=case_id,
        timestamp=current_time,
        action="human_resolved",
        reasoning=f"Resolution: {payload.action_taken}. Notes: {payload.resolution_notes}",
        outcome="success" if (payload.amount_collected or 0) > 0 else "closed",
        amount_recovered=payload.amount_collected,
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Case {case_id} resolved successfully."}
