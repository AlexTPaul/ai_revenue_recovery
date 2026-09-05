from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class DecisionResult:
    action: str  # "schedule_retry" | "route_to_ptp" | "escalate"
    scheduled_at: Optional[datetime]
    rule_id: str
    decision_summary: str
    next_attempt_number: int


def calculate_salary_retry_date(salary_credit_day: int, current_date: datetime) -> datetime:
    """
    Calculates the closest upcoming salary credit date + 2-day liquidity buffer at 10:00 AM.
    salary_credit_day: Integer (1-28).
    """
    buffer_days = 2
    year = current_date.year
    month = current_date.month

    # Bound salary credit day to 1-28 for safe month math
    clamped_day = max(1, min(28, salary_credit_day))

    try:
        current_month_salary = datetime(year, month, clamped_day, 10, 0, 0)
    except ValueError:
        current_month_salary = datetime(year, month, 28, 10, 0, 0)

    # If current date is strictly before the salary date of this month
    if current_date < current_month_salary:
        target_salary_date = current_month_salary
    else:
        # Move to next month's cycle
        if month == 12:
            target_salary_date = datetime(year + 1, 1, clamped_day, 10, 0, 0)
        else:
            target_salary_date = datetime(year, month + 1, clamped_day, 10, 0, 0)

    # Add 2-day buffer for bank clearing/salary liquidity
    retry_date = target_salary_date + timedelta(days=buffer_days)
    return retry_date


def evaluate_mandate_decision(
    failure_reason: str,
    attempt_number: int,
    salary_credit_day: int,
    current_time: datetime,
) -> DecisionResult:
    """
    Deterministic Decision Engine Policy Table.
    Strictly hardcoded state machine enforcing banking bounds.
    """
    # 1. Permanently Closed Account (Dead End)
    if failure_reason == "account_closed":
        return DecisionResult(
            action="escalate",
            scheduled_at=None,
            rule_id="RULE_ACCOUNT_CLOSED_TERMINAL",
            decision_summary="Bank account permanently closed. Bypassing retry & PTP directly to human queue.",
            next_attempt_number=attempt_number,
        )

    # 2. Expired Mandate (Authorization Lapsed)
    if failure_reason == "mandate_expired":
        return DecisionResult(
            action="route_to_ptp",
            scheduled_at=None,
            rule_id="RULE_MANDATE_EXPIRED_PTP",
            decision_summary="Mandate authorization lapsed. Automated retries disabled; routing immediately to Promise-to-Pay.",
            next_attempt_number=attempt_number,
        )

    # 3. Insufficient Funds (Liquidity Timing)
    if failure_reason == "insufficient_funds":
        if attempt_number < 3:
            retry_time = calculate_salary_retry_date(salary_credit_day, current_time)
            next_attempt = attempt_number + 1
            return DecisionResult(
                action="schedule_retry",
                scheduled_at=retry_time,
                rule_id="RULE_FUNDS_SALARY_BUFFER",
                decision_summary=(
                    f"Insufficient funds (Attempt {attempt_number}/3 failed). Scheduled retry #{next_attempt} "
                    f"for {retry_time.strftime('%Y-%m-%d %H:%M')} (2 days post salary day {salary_credit_day})."
                ),
                next_attempt_number=next_attempt,
            )
        else:
            return DecisionResult(
                action="route_to_ptp",
                scheduled_at=None,
                rule_id="RULE_FUNDS_RETRIES_EXHAUSTED",
                decision_summary="Maximum retries (3/3) exhausted for insufficient funds. Routing to conversational Promise-to-Pay.",
                next_attempt_number=attempt_number,
            )

    # 4. Transient Technical Failures (Bank Timeout / Technical Decline)
    if failure_reason in ["bank_timeout", "technical_decline"]:
        if attempt_number < 2:
            retry_time = current_time + timedelta(days=1)
            next_attempt = attempt_number + 1
            return DecisionResult(
                action="schedule_retry",
                scheduled_at=retry_time,
                rule_id="RULE_TECH_NEXT_DAY",
                decision_summary=(
                    f"Transient network/bank error ({failure_reason}, Attempt {attempt_number}/2). "
                    f"Scheduled retry #{next_attempt} for next day ({retry_time.strftime('%Y-%m-%d %H:%M')})."
                ),
                next_attempt_number=next_attempt,
            )
        else:
            return DecisionResult(
                action="route_to_ptp",
                scheduled_at=None,
                rule_id="RULE_TECH_RETRIES_EXHAUSTED",
                decision_summary=f"Technical retry attempts (2/2) exhausted for {failure_reason}. Routing to conversational Promise-to-Pay.",
                next_attempt_number=attempt_number,
            )

    # 5. Unknown / Default Fallback
    return DecisionResult(
        action="route_to_ptp",
        scheduled_at=None,
        rule_id="RULE_UNKNOWN_FALLBACK",
        decision_summary=f"Unrecognized failure reason '{failure_reason}'. Defaulting to conversational Promise-to-Pay.",
        next_attempt_number=attempt_number,
    )
