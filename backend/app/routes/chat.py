import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.promise import PromiseToPay, ConversationLog
from app.models.customer import Customer
from app.models.audit import AuditLog
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
    ConversationEntry,
)
from app.services.llm_service import llm_service
from app.services.clock_service import clock_service
from app.services.razorpay_service import razorpay_service

router = APIRouter(prefix="/chat", tags=["Promise-to-Pay Chat"])


@router.post("/message", response_model=ChatMessageResponse)
def handle_customer_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    """
    Receives customer reply, invokes LLM / NLU parser, updates Promise-to-Pay record,
    and returns agent response + payment link.
    """
    promise = db.query(PromiseToPay).filter(PromiseToPay.id == payload.promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise record not found")

    customer = db.query(Customer).filter(Customer.id == promise.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    current_time = clock_service.get_current_time(db)

    # 1. Log customer message
    customer_log = ConversationLog(
        id=f"conv_{uuid.uuid4().hex[:8]}",
        promise_id=promise.id,
        sender="customer",
        message=payload.message,
        timestamp=current_time,
    )
    db.add(customer_log)

    # Check if a clarification was previously asked in this conversation
    clarification_count = (
        db.query(ConversationLog)
        .filter(
            ConversationLog.promise_id == promise.id,
            ConversationLog.sender == "agent",
            ConversationLog.message.like("%anumaanit tareekh%"),
        )
        .count()
    )

    # 2. Parse message via LLM / Heuristic Engine
    parsed = llm_service.parse_hinglish_commitment(
        message=payload.message,
        current_date=current_time.date(),
        amount=promise.amount,
        customer_name=customer.name,
        prior_clarification_asked=(clarification_count > 0),
    )

    agent_reply = ""
    payment_link_url = None

    if parsed.has_commitment and parsed.promised_date:
        # Commitment extracted successfully
        promise.promised_date = parsed.promised_date
        promise.status = "open"

        # Generate Razorpay payment link
        plink = razorpay_service.create_payment_link(
            amount=promise.amount,
            customer_name=customer.name,
            customer_phone=customer.phone,
            reference_id=promise.id,
            expire_by_date=parsed.promised_date,
        )
        promise.payment_link_id = plink["id"]
        payment_link_url = plink["short_url"]

        agent_reply = (
            f"Shukriya {customer.name} ji! Humne {parsed.promised_date.strftime('%d %B, %Y')} ka promise note kar liya hai. "
            f"Aap is link se kisi bhi samay payment complete kar sakte hain: {payment_link_url}"
        )

        # Log to Audit
        audit = AuditLog(
            id=f"aud_{uuid.uuid4().hex[:8]}",
            entity_type="promise_to_pay",
            entity_id=promise.id,
            timestamp=current_time,
            action="commitment_recorded",
            reasoning=f"Customer confirmed promise to pay by {parsed.promised_date}. Issued payment link {plink['id']}.",
            outcome="success",
            amount_recovered=None,
        )
        db.add(audit)

    elif parsed.is_ambiguous:
        if clarification_count == 0:
            agent_reply = (
                parsed.clarification_message
                or f"Dhanyawad {customer.name} ji! Kya aap koi anumaanit tareekh bata sakte hain taaki hum tab tak link active rakhein?"
            )
        else:
            # Single clarification gate exceeded -> escalate
            promise.status = "escalated"
            agent_reply = (
                f"Samajh gaya {customer.name} ji. Humne aapka case support team ko handoff kar diya hai. "
                "Hamare executive aapse call par sampark karenge."
            )
            audit = AuditLog(
                id=f"aud_{uuid.uuid4().hex[:8]}",
                entity_type="promise_to_pay",
                entity_id=promise.id,
                timestamp=current_time,
                action="escalated",
                reasoning="Ambiguity unresolved after single clarification turn. Escalated to human queue.",
                outcome="escalated",
                amount_recovered=None,
            )
            db.add(audit)

    elif parsed.refused:
        promise.status = "escalated"
        agent_reply = (
            f"Dhanyawad {customer.name} ji. Aapki request note kar li gayi hai. "
            "Hum is mandate ko pause kar rahe hain aur hamari team aapse sampark karegi."
        )
        audit = AuditLog(
            id=f"aud_{uuid.uuid4().hex[:8]}",
            entity_type="promise_to_pay",
            entity_id=promise.id,
            timestamp=current_time,
            action="escalated",
            reasoning="Customer explicitly refused to pay. Halted automated outreach; escalated to human collections.",
            outcome="escalated",
            amount_recovered=None,
        )
        db.add(audit)

    # 3. Log agent reply
    agent_log = ConversationLog(
        id=f"conv_{uuid.uuid4().hex[:8]}",
        promise_id=promise.id,
        sender="agent",
        message=agent_reply,
        timestamp=current_time,
    )
    db.add(agent_log)

    db.commit()

    return ChatMessageResponse(
        status="success",
        agent_reply=agent_reply,
        extracted_data=parsed,
        promise_status=promise.status,
        payment_link=payment_link_url,
    )


@router.get("/{promise_id}/history", response_model=ChatHistoryResponse)
def get_chat_history(promise_id: str, db: Session = Depends(get_db)):
    """Retrieves full conversation history for a Promise-to-Pay chat drawer."""
    promise = db.query(PromiseToPay).filter(PromiseToPay.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")

    customer = promise.customer
    messages = (
        db.query(ConversationLog)
        .filter(ConversationLog.promise_id == promise_id)
        .order_by(ConversationLog.timestamp)
        .all()
    )

    return ChatHistoryResponse(
        promise_id=promise.id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        amount=promise.amount,
        promised_date=promise.promised_date,
        status=promise.status,
        payment_link=f"https://rzp.io/i/{promise.payment_link_id}" if promise.payment_link_id else None,
        messages=[ConversationEntry.model_validate(msg) for msg in messages],
    )
