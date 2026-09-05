from datetime import datetime
from app.services.decision_engine import evaluate_mandate_decision, calculate_salary_retry_date


def test_salary_retry_calculation():
    # Simulated current date: 2026-08-28. Customer salary date: 1st
    current_date = datetime(2026, 8, 28, 10, 0, 0)
    retry_date = calculate_salary_retry_date(salary_credit_day=1, current_date=current_date)
    # Expected: Next salary is Sept 1 + 2 days = Sept 3
    assert retry_date.year == 2026
    assert retry_date.month == 9
    assert retry_date.day == 3

    # Simulated current date: 2026-09-02. Customer salary date: 5th
    current_date = datetime(2026, 9, 2, 10, 0, 0)
    retry_date = calculate_salary_retry_date(salary_credit_day=5, current_date=current_date)
    # Expected: Sept 5 + 2 days = Sept 7
    assert retry_date.day == 7


def test_insufficient_funds_retry_bounds():
    current_time = datetime(2026, 9, 1, 10, 0, 0)

    # Attempt 1: Should schedule retry
    dec1 = evaluate_mandate_decision(
        failure_reason="insufficient_funds",
        attempt_number=1,
        salary_credit_day=5,
        current_time=current_time,
    )
    assert dec1.action == "schedule_retry"
    assert dec1.next_attempt_number == 2
    assert dec1.scheduled_at is not None

    # Attempt 2: Should schedule retry
    dec2 = evaluate_mandate_decision(
        failure_reason="insufficient_funds",
        attempt_number=2,
        salary_credit_day=5,
        current_time=current_time,
    )
    assert dec2.action == "schedule_retry"
    assert dec2.next_attempt_number == 3

    # Attempt 3: Cap reached -> Must route to PTP
    dec3 = evaluate_mandate_decision(
        failure_reason="insufficient_funds",
        attempt_number=3,
        salary_credit_day=5,
        current_time=current_time,
    )
    assert dec3.action == "route_to_ptp"
    assert dec3.rule_id == "RULE_FUNDS_RETRIES_EXHAUSTED"


def test_technical_decline_bounds():
    current_time = datetime(2026, 9, 1, 10, 0, 0)

    # Attempt 1: Next-day retry
    dec1 = evaluate_mandate_decision(
        failure_reason="bank_timeout",
        attempt_number=1,
        salary_credit_day=1,
        current_time=current_time,
    )
    assert dec1.action == "schedule_retry"
    assert dec1.scheduled_at.day == 2

    # Attempt 2: Cap reached -> Route to PTP
    dec2 = evaluate_mandate_decision(
        failure_reason="bank_timeout",
        attempt_number=2,
        salary_credit_day=1,
        current_time=current_time,
    )
    assert dec2.action == "route_to_ptp"


def test_mandate_expired_bypasses_retries():
    current_time = datetime(2026, 9, 1, 10, 0, 0)
    dec = evaluate_mandate_decision(
        failure_reason="mandate_expired",
        attempt_number=1,
        salary_credit_day=1,
        current_time=current_time,
    )
    assert dec.action == "route_to_ptp"
    assert dec.rule_id == "RULE_MANDATE_EXPIRED_PTP"


def test_account_closed_immediate_escalation():
    current_time = datetime(2026, 9, 1, 10, 0, 0)
    dec = evaluate_mandate_decision(
        failure_reason="account_closed",
        attempt_number=1,
        salary_credit_day=1,
        current_time=current_time,
    )
    assert dec.action == "escalate"
    assert dec.rule_id == "RULE_ACCOUNT_CLOSED_TERMINAL"
