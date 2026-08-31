# 03. Decision Engine & Deterministic Rules

## 1. The Core Policy Philosophy

In financial revenue recovery, unbounded agent autonomy is dangerous. If an AI model hallucinates or loops indefinitely:
- Bank accounts can be subjected to illegal recurring charge attempts.
- Customers can be spammed with aggressive collection messages.
- Merchants can face regulatory penalties or interchange blacklisting.

To solve this, the **Decision Engine** is implemented as a **100% deterministic, pure Python state machine**. The LLM is strictly isolated from making routing choices.

---

## 2. Decision Engine Policy Matrix

| Failure Code | Attempt Count | Action Taken | Target Timing Formula | Next State |
| :--- | :--- | :--- | :--- | :--- |
| `insufficient_funds` | $1 \le \text{Attempt} < 3$ | `schedule_retry` | $\text{Next Salary Date} + 2 \text{ days}$ | `retry_scheduled` |
| `insufficient_funds` | $\text{Attempt} \ge 3$ | `route_to_ptp` | Immediate | `ptp_negotiation` |
| `bank_timeout` | $\text{Attempt} < 2$ | `schedule_retry` | $\text{Current Time} + 1 \text{ day}$ | `retry_scheduled` |
| `bank_timeout` | $\text{Attempt} \ge 2$ | `route_to_ptp` | Immediate | `ptp_negotiation` |
| `technical_decline` | $\text{Attempt} < 2$ | `schedule_retry` | $\text{Current Time} + 1 \text{ day}$ | `retry_scheduled` |
| `technical_decline` | $\text{Attempt} \ge 2$ | `route_to_ptp` | Immediate | `ptp_negotiation` |
| `mandate_expired` | Any | `route_to_ptp` | Immediate (Retries bypassed) | `ptp_negotiation` |
| `account_closed` | Any | `escalate_directly`| Immediate (PTP bypassed) | `escalated_to_human` |

---

## 3. Detailed Logic & Scheduling Algorithms

### 3.1 Salary Cycle Retry Scheduling Formula
When a mandate fails due to `insufficient_funds`, retrying the next day is usually futile because the customer has not received their paycheck yet.

The algorithm schedules the next attempt **2 days after the customer's salary credit day** to ensure liquidity is settled:

```python
from datetime import datetime, timedelta

def calculate_salary_retry_date(salary_credit_day: int, current_date: datetime) -> datetime:
    """
    Computes the closest upcoming salary date + 2-day liquidity buffer.
    salary_credit_day: Integer between 1 and 28.
    """
    buffer_days = 2
    year = current_date.year
    month = current_date.month

    # Construct salary date for the current month
    try:
        current_month_salary = datetime(year, month, salary_credit_day, 10, 0, 0)
    except ValueError:
        # Fallback for short months (e.g. Feb 28)
        current_month_salary = datetime(year, month, 28, 10, 0, 0)

    # If current date is before salary date of this month:
    if current_date < current_month_salary:
        target_salary_date = current_month_salary
    else:
        # Move to next month's salary cycle
        if month == 12:
            target_salary_date = datetime(year + 1, 1, salary_credit_day, 10, 0, 0)
        else:
            target_salary_date = datetime(year, month + 1, salary_credit_day, 10, 0, 0)

    # Add 2-day buffer for bank clearing/settlement
    retry_date = target_salary_date + timedelta(days=buffer_days)
    return retry_date
```

### 3.2 Transient Technical Failure Scheduling
For transient errors (`bank_timeout`, `technical_decline`):
$$\text{Retry Date} = \text{Current Simulated Date} + 1 \text{ Day at 10:00 AM}$$
Max attempts permitted: **2**. If both fail, route directly to Promise-to-Pay.

### 3.3 Terminal Conditions (Stopping Rules)
1. **Max Retry Rule:**
   - `insufficient_funds`: At most 3 automated retries.
   - `technical_decline` / `bank_timeout`: At most 2 automated retries.
2. **Expired Mandate Rule:**
   - A lapsed mandate cannot be re-debited without customer re-authorization. Retries are completely skipped.
3. **Closed Account Rule:**
   - A closed bank account is a permanent failure. Bypasses both retry and conversational PTP, immediately routing to human operations.
4. **Grace Nudge Stopping Rule:**
   - When a Promise-to-Pay is broken, exactly **1** grace nudge is sent.
   - If unpaid after the grace period, the agent **permanently stops** automated outreach and triggers human escalation.

---

## 4. Decision Engine Implementation Reference

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class DecisionResult:
    action: str  # "schedule_retry" | "route_to_ptp" | "escalate"
    scheduled_at: Optional[datetime]
    rule_id: str
    decision_summary: str

def evaluate_decision(
    failure_reason: str,
    attempt_number: int,
    salary_credit_day: int,
    current_time: datetime
) -> DecisionResult:
    
    if failure_reason == "account_closed":
        return DecisionResult(
            action="escalate",
            scheduled_at=None,
            rule_id="RULE_ACCOUNT_CLOSED_TERMINAL",
            decision_summary="Bank account permanently closed. Bypassing retry & PTP directly to human queue."
        )

    if failure_reason == "mandate_expired":
        return DecisionResult(
            action="route_to_ptp",
            scheduled_at=None,
            rule_id="RULE_MANDATE_EXPIRED_PTP",
            decision_summary="Mandate authorization lapsed. Retries disabled; routing to conversational Promise-to-Pay."
        )

    if failure_reason == "insufficient_funds":
        if attempt_number < 3:
            retry_time = calculate_salary_retry_date(salary_credit_day, current_time)
            return DecisionResult(
                action="schedule_retry",
                scheduled_at=retry_time,
                rule_id="RULE_FUNDS_SALARY_BUFFER",
                decision_summary=f"Insufficient funds (Attempt {attempt_number}/3). Scheduled retry for {retry_time.strftime('%Y-%m-%d')} (Salary day {salary_credit_day} + 2d buffer)."
            )
        else:
            return DecisionResult(
                action="route_to_ptp",
                scheduled_at=None,
                rule_id="RULE_FUNDS_RETRIES_EXHAUSTED",
                decision_summary=f"Max retries (3/3) exhausted for insufficient funds. Routing to conversational Promise-to-Pay."
            )

    if failure_reason in ["bank_timeout", "technical_decline"]:
        if attempt_number < 2:
            retry_time = current_time + timedelta(days=1)
            return DecisionResult(
                action="schedule_retry",
                scheduled_at=retry_time,
                rule_id="RULE_TECH_NEXT_DAY",
                decision_summary=f"Transient technical error ({failure_reason}, Attempt {attempt_number}/2). Retrying next day at {retry_time.strftime('%Y-%m-%d')}."
            )
        else:
            return DecisionResult(
                action="route_to_ptp",
                scheduled_at=None,
                rule_id="RULE_TECH_RETRIES_EXHAUSTED",
                decision_summary=f"Technical retries (2/2) exhausted. Routing to conversational Promise-to-Pay."
            )

    # Fallback default
    return DecisionResult(
        action="route_to_ptp",
        scheduled_at=None,
        rule_id="RULE_UNKNOWN_FALLBACK",
        decision_summary="Unrecognized failure reason; falling back to Promise-to-Pay."
    )
```
