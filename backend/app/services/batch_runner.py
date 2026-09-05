import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.mandate import MandateAttempt
from app.models.promise import PromiseToPay, ConversationLog
from app.models.audit import AuditLog
from app.models.clock import VirtualClock
from app.services.decision_engine import evaluate_mandate_decision
from app.services.llm_service import llm_service


SAMPLE_CASES = [
    {
        "id": "cust_001",
        "name": "Rahul Sharma",
        "phone": "+91 98201 11223",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_001",
        "amount": 4999.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 1,
    },
    {
        "id": "cust_002",
        "name": "Priya Menon",
        "phone": "+91 98450 33445",
        "salary_credit_day": 5,
        "mandate_id": "mandate_rzp_002",
        "amount": 1299.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 1,
    },
    {
        "id": "cust_003",
        "name": "Amit Kumar",
        "phone": "+91 97110 55667",
        "salary_credit_day": 15,
        "mandate_id": "mandate_rzp_003",
        "amount": 899.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 1,
    },
    {
        "id": "cust_004",
        "name": "Neha Gupta",
        "phone": "+91 99302 77889",
        "salary_credit_day": 25,
        "mandate_id": "mandate_rzp_004",
        "amount": 2499.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 1,
    },
    {
        "id": "cust_005",
        "name": "Vikram Singh",
        "phone": "+91 98190 99001",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_005",
        "amount": 3499.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 3,  # Max retries reached -> Should route to PTP
    },
    {
        "id": "cust_006",
        "name": "Ananya Roy",
        "phone": "+91 98311 22334",
        "salary_credit_day": 10,
        "mandate_id": "mandate_rzp_006",
        "amount": 799.0,
        "failure_reason": "bank_timeout",
        "attempt_number": 1,  # Transient error -> Next-day retry
    },
    {
        "id": "cust_007",
        "name": "Karan Patel",
        "phone": "+91 98250 44556",
        "salary_credit_day": 5,
        "mandate_id": "mandate_rzp_007",
        "amount": 1599.0,
        "failure_reason": "technical_decline",
        "attempt_number": 1,  # Transient error -> Next-day retry
    },
    {
        "id": "cust_008",
        "name": "Ritu Verma",
        "phone": "+91 99100 66778",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_008",
        "amount": 999.0,
        "failure_reason": "bank_timeout",
        "attempt_number": 2,  # Technical retries exhausted -> Route to PTP
    },
    {
        "id": "cust_009",
        "name": "Rohan Mehta",
        "phone": "+91 98210 88990",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_009",
        "amount": 5999.0,
        "failure_reason": "mandate_expired",
        "attempt_number": 1,  # Mandate expired -> Retries bypassed to PTP
    },
    {
        "id": "cust_010",
        "name": "Kavita Iyer",
        "phone": "+91 94440 11223",
        "salary_credit_day": 10,
        "mandate_id": "mandate_rzp_010",
        "amount": 1999.0,
        "failure_reason": "mandate_expired",
        "attempt_number": 1,  # Mandate expired -> Retries bypassed to PTP
    },
    {
        "id": "cust_011",
        "name": "Deepak Joshi",
        "phone": "+91 98220 33445",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_011",
        "amount": 4500.0,
        "failure_reason": "account_closed",
        "attempt_number": 1,  # Dead end -> Immediate escalation to human queue
    },
    {
        "id": "cust_012",
        "name": "Sunita Rao",
        "phone": "+91 98490 55667",
        "salary_credit_day": 5,
        "mandate_id": "mandate_rzp_012",
        "amount": 2200.0,
        "failure_reason": "account_closed",
        "attempt_number": 1,  # Dead end -> Immediate escalation to human queue
    },
    {
        "id": "cust_013",
        "name": "Manoj Tiwari",
        "phone": "+91 99550 77889",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_013",
        "amount": 1499.0,
        "failure_reason": "insufficient_funds",
        "attempt_number": 1,
    },
    {
        "id": "cust_014",
        "name": "Pooja Nair",
        "phone": "+91 98470 99001",
        "salary_credit_day": 7,
        "mandate_id": "mandate_rzp_014",
        "amount": 3199.0,
        "failure_reason": "technical_decline",
        "attempt_number": 1,
    },
    {
        "id": "cust_015",
        "name": "Siddharth Jain",
        "phone": "+91 98110 12345",
        "salary_credit_day": 1,
        "mandate_id": "mandate_rzp_015",
        "amount": 4299.0,
        "failure_reason": "mandate_expired",
        "attempt_number": 1,
    },
]


class BatchRunnerService:
    def reset_and_seed_batch(self, db: Session, case_count: int = 15) -> Dict[str, Any]:
        """Cleans existing simulation state and seeds fresh, diverse test cases."""
        # 1. Clear existing database records
        db.query(ConversationLog).delete()
        db.query(AuditLog).delete()
        db.query(PromiseToPay).delete()
        db.query(MandateAttempt).delete()
        db.query(Customer).delete()

        # Reset clock
        start_time = datetime(2026, 9, 1, 10, 0, 0)
        clock = db.query(VirtualClock).filter(VirtualClock.id == 1).first()
        if not clock:
            clock = VirtualClock(id=1, current_time=start_time, is_active=True)
            db.add(clock)
        else:
            clock.current_time = start_time

        db.commit()

        cases_to_load = SAMPLE_CASES[:case_count]
        total_at_risk = 0.0
        retries_scheduled = 0
        ptp_routed = 0
        escalated_immediately = 0

        for item in cases_to_load:
            total_at_risk += item["amount"]

            # Create Customer
            customer = Customer(
                id=item["id"],
                name=item["name"],
                phone=item["phone"],
                salary_credit_day=item["salary_credit_day"],
                mandate_id=item["mandate_id"],
                created_at=start_time - timedelta(days=30),
            )
            db.add(customer)

            # Evaluate decision through deterministic engine
            decision = evaluate_mandate_decision(
                failure_reason=item["failure_reason"],
                attempt_number=item["attempt_number"],
                salary_credit_day=item["salary_credit_day"],
                current_time=start_time,
            )

            attempt_id = f"att_{uuid.uuid4().hex[:8]}"

            # Determine attempt status & scheduled time
            if decision.action == "schedule_retry":
                retries_scheduled += 1
                attempt = MandateAttempt(
                    id=attempt_id,
                    customer_id=customer.id,
                    amount=item["amount"],
                    attempt_number=item["attempt_number"],
                    scheduled_at=decision.scheduled_at,
                    status="pending",
                    failure_reason=item["failure_reason"],
                    decision_explanation=decision.decision_summary,
                    next_action="retry_scheduled",
                )
                db.add(attempt)

                audit = AuditLog(
                    id=f"aud_{uuid.uuid4().hex[:8]}",
                    entity_type="mandate_attempt",
                    entity_id=attempt_id,
                    timestamp=start_time,
                    action="retry_scheduled",
                    reasoning=decision.decision_summary,
                    outcome="pending",
                    amount_recovered=None,
                )
                db.add(audit)

            elif decision.action == "route_to_ptp":
                ptp_routed += 1
                attempt = MandateAttempt(
                    id=attempt_id,
                    customer_id=customer.id,
                    amount=item["amount"],
                    attempt_number=item["attempt_number"],
                    scheduled_at=start_time,
                    executed_at=start_time,
                    status="failed",
                    failure_reason=item["failure_reason"],
                    decision_explanation=decision.decision_summary,
                    next_action="route_to_ptp",
                )
                db.add(attempt)

                ptp_id = f"ptp_{uuid.uuid4().hex[:8]}"
                due_date = (start_time + timedelta(days=3)).date()
                ptp = PromiseToPay(
                    id=ptp_id,
                    customer_id=customer.id,
                    mandate_attempt_id=attempt_id,
                    amount=item["amount"],
                    promised_date=due_date,
                    status="open",
                    grace_nudge_sent=False,
                    payment_link_id=f"plink_{uuid.uuid4().hex[:6]}",
                    created_at=start_time,
                )
                db.add(ptp)

                # Initial conversation nudge in Hinglish
                conv = ConversationLog(
                    id=f"conv_{uuid.uuid4().hex[:8]}",
                    promise_id=ptp_id,
                    sender="agent",
                    message=(
                        f"Namaste {customer.name} ji, aapka ₹{item['amount']:,.2f} ka mandate charge process nahi ho paya "
                        f"({item['failure_reason'].replace('_', ' ')}). Kya aap bata sakte hain ki aap kab tak pay kar payenge?"
                    ),
                    timestamp=start_time,
                )
                db.add(conv)

                audit = AuditLog(
                    id=f"aud_{uuid.uuid4().hex[:8]}",
                    entity_type="promise_to_pay",
                    entity_id=ptp_id,
                    timestamp=start_time,
                    action="route_to_ptp",
                    reasoning=decision.decision_summary,
                    outcome="pending",
                    amount_recovered=None,
                )
                db.add(audit)

            elif decision.action == "escalate":
                escalated_immediately += 1
                attempt = MandateAttempt(
                    id=attempt_id,
                    customer_id=customer.id,
                    amount=item["amount"],
                    attempt_number=item["attempt_number"],
                    scheduled_at=start_time,
                    executed_at=start_time,
                    status="failed",
                    failure_reason=item["failure_reason"],
                    decision_explanation=decision.decision_summary,
                    next_action="escalate",
                )
                db.add(attempt)

                audit = AuditLog(
                    id=f"aud_{uuid.uuid4().hex[:8]}",
                    entity_type="mandate_attempt",
                    entity_id=attempt_id,
                    timestamp=start_time,
                    action="escalated",
                    reasoning=decision.decision_summary,
                    outcome="escalated",
                    amount_recovered=None,
                )
                db.add(audit)

        db.commit()

        return {
            "total_cases_loaded": len(cases_to_load),
            "simulated_date": start_time.isoformat(),
            "summary": {
                "total_at_risk": total_at_risk,
                "retries_scheduled": retries_scheduled,
                "ptp_routed": ptp_routed,
                "escalated_immediately": escalated_immediately,
            }
        }


batch_runner_service = BatchRunnerService()
