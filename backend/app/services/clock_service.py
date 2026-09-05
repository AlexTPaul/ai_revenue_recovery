import uuid
import random
from datetime import datetime, timedelta, date
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.clock import VirtualClock
from app.models.mandate import MandateAttempt
from app.models.promise import PromiseToPay, ConversationLog
from app.models.audit import AuditLog
from app.models.customer import Customer
from app.schemas.clock import SimulationEvent
from app.services.decision_engine import evaluate_mandate_decision
from app.services.llm_service import llm_service


class ClockService:
    DEFAULT_START_TIME = datetime(2026, 9, 1, 10, 0, 0)

    def get_or_create_clock(self, db: Session) -> VirtualClock:
        clock = db.query(VirtualClock).filter(VirtualClock.id == 1).first()
        if not clock:
            clock = VirtualClock(id=1, current_time=self.DEFAULT_START_TIME, is_active=True)
            db.add(clock)
            db.commit()
            db.refresh(clock)
        return clock

    def get_current_time(self, db: Session) -> datetime:
        return self.get_or_create_clock(db).current_time

    def reset_clock(self, db: Session) -> VirtualClock:
        clock = self.get_or_create_clock(db)
        clock.current_time = self.DEFAULT_START_TIME
        db.commit()
        db.refresh(clock)
        return clock

    def fast_forward(self, db: Session, days: int = 1, hours: int = 0) -> Tuple[datetime, datetime, List[SimulationEvent]]:
        clock = self.get_or_create_clock(db)
        previous_time = clock.current_time
        new_time = previous_time + timedelta(days=days, hours=hours)
        clock.current_time = new_time
        db.commit()

        events_processed: List[SimulationEvent] = []

        # 1. Process Pending Mandate Retries that matured before or at new_time
        events_processed.extend(self._process_matured_retries(db, new_time))

        # 2. Process Maturing Promises to Pay
        events_processed.extend(self._process_matured_promises(db, new_time))

        db.commit()
        return previous_time, new_time, events_processed

    def _process_matured_retries(self, db: Session, current_time: datetime) -> List[SimulationEvent]:
        events: List[SimulationEvent] = []
        pending_attempts = (
            db.query(MandateAttempt)
            .filter(
                MandateAttempt.status == "pending",
                MandateAttempt.scheduled_at <= current_time
            )
            .all()
        )

        for attempt in pending_attempts:
            customer = db.query(Customer).filter(Customer.id == attempt.customer_id).first()
            if not customer:
                continue

            # Deterministic simulation of retry success/failure
            is_success = False
            if attempt.failure_reason in ["bank_timeout", "technical_decline"]:
                is_success = True  # Technical retry next day succeeds
            elif attempt.failure_reason == "insufficient_funds":
                # If current simulated day is within salary liquidity window (salary_day to salary_day + 5)
                sim_day = attempt.scheduled_at.day
                sal_day = customer.salary_credit_day
                if sal_day <= sim_day <= (sal_day + 6) or (sal_day >= 25 and sim_day <= 5):
                    is_success = True
                else:
                    is_success = (attempt.attempt_number >= 2)

            if is_success:
                attempt.status = "success"
                attempt.executed_at = attempt.scheduled_at
                attempt.next_action = "none"

                # Log recovery to audit log
                audit = AuditLog(
                    id=f"aud_{uuid.uuid4().hex[:8]}",
                    entity_type="mandate_attempt",
                    entity_id=attempt.id,
                    timestamp=attempt.scheduled_at,
                    action="recovered",
                    reasoning=f"Scheduled mandate retry #{attempt.attempt_number} succeeded. ₹{attempt.amount:,.2f} recovered.",
                    outcome="success",
                    amount_recovered=attempt.amount,
                )
                db.add(audit)

                events.append(SimulationEvent(
                    event_type="retry_succeeded",
                    entity_id=attempt.id,
                    description=f"Mandate retry #{attempt.attempt_number} succeeded for {customer.name} (₹{attempt.amount:,.2f})",
                    outcome="recovered",
                    amount_recovered=attempt.amount,
                ))
            else:
                # Retry failed - evaluate next step
                attempt.status = "failed"
                attempt.executed_at = attempt.scheduled_at

                decision = evaluate_mandate_decision(
                    failure_reason=attempt.failure_reason or "insufficient_funds",
                    attempt_number=attempt.attempt_number,
                    salary_credit_day=customer.salary_credit_day,
                    current_time=attempt.scheduled_at,
                )

                if decision.action == "schedule_retry":
                    new_attempt_id = f"att_{uuid.uuid4().hex[:8]}"
                    next_attempt = MandateAttempt(
                        id=new_attempt_id,
                        customer_id=customer.id,
                        amount=attempt.amount,
                        attempt_number=decision.next_attempt_number,
                        scheduled_at=decision.scheduled_at,
                        status="pending",
                        failure_reason=attempt.failure_reason,
                        decision_explanation=decision.decision_summary,
                        next_action="retry_scheduled",
                    )
                    db.add(next_attempt)

                    audit = AuditLog(
                        id=f"aud_{uuid.uuid4().hex[:8]}",
                        entity_type="mandate_attempt",
                        entity_id=new_attempt_id,
                        timestamp=attempt.scheduled_at,
                        action="retry_scheduled",
                        reasoning=decision.decision_summary,
                        outcome="pending",
                        amount_recovered=None,
                    )
                    db.add(audit)

                    events.append(SimulationEvent(
                        event_type="retry_rescheduled",
                        entity_id=new_attempt_id,
                        description=f"Retry #{decision.next_attempt_number} scheduled for {customer.name} on {decision.scheduled_at.strftime('%Y-%m-%d')}",
                        outcome="pending",
                        amount_recovered=0.0,
                    ))

                elif decision.action == "route_to_ptp":
                    attempt.next_action = "route_to_ptp"
                    ptp_id = f"ptp_{uuid.uuid4().hex[:8]}"
                    due_date = (attempt.scheduled_at + timedelta(days=3)).date()
                    ptp = PromiseToPay(
                        id=ptp_id,
                        customer_id=customer.id,
                        mandate_attempt_id=attempt.id,
                        amount=attempt.amount,
                        promised_date=due_date,
                        status="open",
                        grace_nudge_sent=False,
                        payment_link_id=f"plink_{uuid.uuid4().hex[:6]}",
                    )
                    db.add(ptp)

                    # Initial conversation entry
                    conv = ConversationLog(
                        id=f"conv_{uuid.uuid4().hex[:8]}",
                        promise_id=ptp_id,
                        sender="agent",
                        message=(
                            f"Namaste {customer.name} ji, aapka ₹{attempt.amount:,.2f} ka payment mandate se process nahi ho paya. "
                            f"Kya aap bata sakte hain ki aap kab tak pay kar payenge?"
                        ),
                        timestamp=attempt.scheduled_at,
                    )
                    db.add(conv)

                    audit = AuditLog(
                        id=f"aud_{uuid.uuid4().hex[:8]}",
                        entity_type="promise_to_pay",
                        entity_id=ptp_id,
                        timestamp=attempt.scheduled_at,
                        action="route_to_ptp",
                        reasoning=decision.decision_summary,
                        outcome="pending",
                        amount_recovered=None,
                    )
                    db.add(audit)

                    events.append(SimulationEvent(
                        event_type="routed_to_ptp",
                        entity_id=ptp_id,
                        description=f"Retries exhausted for {customer.name}. Routed to Hinglish Promise-to-Pay chat.",
                        outcome="ptp_open",
                        amount_recovered=0.0,
                    ))

                elif decision.action == "escalate":
                    attempt.next_action = "escalate"
                    audit = AuditLog(
                        id=f"aud_{uuid.uuid4().hex[:8]}",
                        entity_type="mandate_attempt",
                        entity_id=attempt.id,
                        timestamp=attempt.scheduled_at,
                        action="escalated",
                        reasoning=decision.decision_summary,
                        outcome="escalated",
                        amount_recovered=None,
                    )
                    db.add(audit)

                    events.append(SimulationEvent(
                        event_type="escalated",
                        entity_id=attempt.id,
                        description=f"Mandate for {customer.name} permanently escalated to human queue: {decision.decision_summary}",
                        outcome="escalated",
                        amount_recovered=0.0,
                    ))

        return events

    def _process_matured_promises(self, db: Session, current_time: datetime) -> List[SimulationEvent]:
        events: List[SimulationEvent] = []
        current_sim_date = current_time.date()

        open_promises = db.query(PromiseToPay).filter(PromiseToPay.status == "open").all()

        for promise in open_promises:
            customer = db.query(Customer).filter(Customer.id == promise.customer_id).first()
            if not customer:
                continue

            # Check if promised date has arrived or passed
            if current_sim_date > promise.promised_date:
                # Check if grace nudge was already sent
                if not promise.grace_nudge_sent:
                    # Send 1 Grace Nudge
                    promise.grace_nudge_sent = True

                    conv = ConversationLog(
                        id=f"conv_{uuid.uuid4().hex[:8]}",
                        promise_id=promise.id,
                        sender="agent",
                        message=(
                            f"Namaste {customer.name} ji, aapne {promise.promised_date.strftime('%d %B')} ko ₹{promise.amount:,.2f} "
                            f"pay karne ka commitment diya tha. Kripya is link se payment complete karein: https://rzp.io/i/{promise.payment_link_id}"
                        ),
                        timestamp=current_time,
                    )
                    db.add(conv)

                    audit = AuditLog(
                        id=f"aud_{uuid.uuid4().hex[:8]}",
                        entity_type="promise_to_pay",
                        entity_id=promise.id,
                        timestamp=current_time,
                        action="grace_nudge_sent",
                        reasoning=f"Promised date ({promise.promised_date}) passed without payment. Dispatched single compliant grace nudge.",
                        outcome="pending",
                        amount_recovered=None,
                    )
                    db.add(audit)

                    events.append(SimulationEvent(
                        event_type="grace_nudge_sent",
                        entity_id=promise.id,
                        description=f"Grace nudge sent to {customer.name} for promised date {promise.promised_date}",
                        outcome="grace_nudge_sent",
                        amount_recovered=0.0,
                    ))

                elif promise.grace_nudge_sent and (current_sim_date - promise.promised_date).days >= 2:
                    # Grace period also expired -> Stopping rule triggered: Escalate to human queue
                    promise.status = "escalated"

                    audit = AuditLog(
                        id=f"aud_{uuid.uuid4().hex[:8]}",
                        entity_type="promise_to_pay",
                        entity_id=promise.id,
                        timestamp=current_time,
                        action="escalated",
                        reasoning=(
                            "Stopping Rule Triggered: Commitment unfulfilled after promised date and single grace nudge. "
                            "Automated agent outreach halted; escalated to human collection queue."
                        ),
                        outcome="escalated",
                        amount_recovered=None,
                    )
                    db.add(audit)

                    events.append(SimulationEvent(
                        event_type="stopping_rule_escalated",
                        entity_id=promise.id,
                        description=f"Stopping rule enforced: {customer.name} unfulfilled post-grace nudge. Handoff to human queue.",
                        outcome="escalated",
                        amount_recovered=0.0,
                    ))

        return events


clock_service = ClockService()
