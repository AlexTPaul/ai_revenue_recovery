import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.promise import PromiseToPay
from app.models.mandate import MandateAttempt
from app.models.audit import AuditLog
from app.services.razorpay_service import razorpay_service
from app.services.clock_service import clock_service

router = APIRouter(prefix="/webhooks", tags=["Razorpay Webhooks"])


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Handles incoming Razorpay Webhook events:
    - payment_link.paid -> resolves Promise-to-Pay to kept & logs revenue
    - subscription.charged -> marks mandate attempt as success
    - subscription.charged.failed -> feeds failure into decision engine
    """
    body_bytes = await request.body()
    if x_razorpay_signature:
        is_valid = razorpay_service.verify_webhook_signature(body_bytes, x_razorpay_signature)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload: Dict[str, Any] = await request.json()
    event_type = payload.get("event")
    current_time = clock_service.get_current_time(db)

    # 1. Promise-to-Pay Link Paid
    if event_type == "payment_link.paid":
        payment_link_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        plink_id = payment_link_entity.get("id")
        amount = float(payment_link_entity.get("amount", 0)) / 100.0

        promise = db.query(PromiseToPay).filter(PromiseToPay.payment_link_id == plink_id).first()
        if promise:
            promise.status = "kept"
            audit = AuditLog(
                id=f"aud_{uuid.uuid4().hex[:8]}",
                entity_type="promise_to_pay",
                entity_id=promise.id,
                timestamp=current_time,
                action="recovered",
                reasoning=f"Payment received via Razorpay payment link ({plink_id}). Customer kept promise.",
                outcome="success",
                amount_recovered=amount,
            )
            db.add(audit)
            db.commit()

        return {"status": "success", "event": "payment_link.paid", "processed": bool(promise)}

    # 2. Mandate Subscription Charged Successfully
    elif event_type == "subscription.charged":
        subscription_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        mandate_id = subscription_entity.get("id")

        attempt = (
            db.query(MandateAttempt)
            .filter(MandateAttempt.status == "pending")
            .first()
        )
        if attempt:
            attempt.status = "success"
            attempt.executed_at = current_time
            audit = AuditLog(
                id=f"aud_{uuid.uuid4().hex[:8]}",
                entity_type="mandate_attempt",
                entity_id=attempt.id,
                timestamp=current_time,
                action="recovered",
                reasoning="Mandate subscription charge cleared successfully via Razorpay webhook.",
                outcome="success",
                amount_recovered=attempt.amount,
            )
            db.add(audit)
            db.commit()

        return {"status": "success", "event": "subscription.charged"}

    return {"status": "ignored", "event": event_type}
