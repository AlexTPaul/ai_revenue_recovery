from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.customer import Customer
from app.models.mandate import MandateAttempt
from app.models.promise import PromiseToPay
from app.models.audit import AuditLog
from app.schemas.cases import CaseListItem, CaseDetailResponse, AuditLogEntry

router = APIRouter(prefix="/cases", tags=["Cases & Audit"])


@router.get("", response_model=List[CaseListItem])
def list_cases(
    status: Optional[str] = Query(None, description="Filter by status (pending, success, failed)"),
    failure_reason: Optional[str] = Query(None, description="Filter by failure reason"),
    db: Session = Depends(get_db),
):
    """Fetches all active mandate recovery cases."""
    query = db.query(MandateAttempt).join(Customer, MandateAttempt.customer_id == Customer.id)

    if status:
        query = query.filter(MandateAttempt.status == status)
    if failure_reason:
        query = query.filter(MandateAttempt.failure_reason == failure_reason)

    attempts = query.order_by(desc(MandateAttempt.scheduled_at)).all()

    result: List[CaseListItem] = []
    for att in attempts:
        customer = att.customer
        # Find active promise if any
        active_promise = (
            db.query(PromiseToPay)
            .filter(PromiseToPay.customer_id == customer.id)
            .order_by(desc(PromiseToPay.created_at))
            .first()
        )

        result.append(
            CaseListItem(
                id=att.id,
                customer_id=customer.id,
                customer_name=customer.name,
                customer_phone=customer.phone,
                amount=att.amount,
                attempt_number=att.attempt_number,
                scheduled_at=att.scheduled_at,
                executed_at=att.executed_at,
                status=att.status,
                failure_reason=att.failure_reason,
                decision_explanation=att.decision_explanation,
                next_action=att.next_action,
                salary_credit_day=customer.salary_credit_day,
                mandate_id=customer.mandate_id,
                active_promise_id=active_promise.id if active_promise else None,
                promise_status=active_promise.status if active_promise else None,
                promised_date=active_promise.promised_date if active_promise else None,
            )
        )

    return result


@router.get("/{attempt_id}", response_model=CaseDetailResponse)
def get_case_detail(attempt_id: str, db: Session = Depends(get_db)):
    """Fetches single case details and complete chronological audit log."""
    att = db.query(MandateAttempt).filter(MandateAttempt.id == attempt_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Case not found")

    customer = att.customer
    active_promise = (
        db.query(PromiseToPay)
        .filter(PromiseToPay.customer_id == customer.id)
        .order_by(desc(PromiseToPay.created_at))
        .first()
    )

    case_item = CaseListItem(
        id=att.id,
        customer_id=customer.id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        amount=att.amount,
        attempt_number=att.attempt_number,
        scheduled_at=att.scheduled_at,
        executed_at=att.executed_at,
        status=att.status,
        failure_reason=att.failure_reason,
        decision_explanation=att.decision_explanation,
        next_action=att.next_action,
        salary_credit_day=customer.salary_credit_day,
        mandate_id=customer.mandate_id,
        active_promise_id=active_promise.id if active_promise else None,
        promise_status=active_promise.status if active_promise else None,
        promised_date=active_promise.promised_date if active_promise else None,
    )

    # Fetch audit logs related to this attempt or customer's promise
    audit_logs = (
        db.query(AuditLog)
        .filter(
            (AuditLog.entity_id == att.id)
            | (AuditLog.entity_id == (active_promise.id if active_promise else ""))
        )
        .order_by(AuditLog.timestamp)
        .all()
    )

    return CaseDetailResponse(
        case=case_item,
        audit_trail=[AuditLogEntry.model_validate(log) for log in audit_logs],
    )


@router.get("/{attempt_id}/audit", response_model=List[AuditLogEntry])
def get_case_audit_trail(attempt_id: str, db: Session = Depends(get_db)):
    """Retrieves full compliance audit trail entries for a case."""
    att = db.query(MandateAttempt).filter(MandateAttempt.id == attempt_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Case not found")

    customer = att.customer
    active_promise = (
        db.query(PromiseToPay)
        .filter(PromiseToPay.customer_id == customer.id)
        .first()
    )

    audit_logs = (
        db.query(AuditLog)
        .filter(
            (AuditLog.entity_id == att.id)
            | (AuditLog.entity_id == (active_promise.id if active_promise else ""))
        )
        .order_by(AuditLog.timestamp)
        .all()
    )

    return [AuditLogEntry.model_validate(log) for log in audit_logs]
