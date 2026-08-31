# 06. API Reference & Gateway Integration

## 1. REST API Architecture (FastAPI)

Base URL: `http://localhost:8000/api`

All JSON responses follow standard HTTP status codes and structured schemas.

---

## 2. API Endpoints

### 2.1 Batch Simulation Endpoints

#### `POST /api/batch/run`
Spawns or re-seeds the 15 simulated failure scenarios and runs the initial evaluation.
- **Request Body:** `{ "case_count": 15 }`
- **Response (200 OK):**
```json
{
  "status": "success",
  "total_cases_loaded": 15,
  "simulated_date": "2026-09-01T10:00:00Z",
  "summary": {
    "total_at_risk": 38450.0,
    "retries_scheduled": 9,
    "ptp_routed": 4,
    "escalated_immediately": 2
  }
}
```

#### `GET /api/batch/summary`
Returns top-level metric counters for the dashboard.
- **Response (200 OK):**
```json
{
  "total_at_risk": 38450.0,
  "total_recovered": 24200.0,
  "recovery_rate_pct": 62.94,
  "total_cases": 15,
  "status_breakdown": {
    "pending_retry": 4,
    "ptp_open": 2,
    "recovered": 6,
    "escalated": 3
  }
}
```

#### `POST /api/batch/reset`
Wipes the current simulation state and resets database to initial clean state.

---

### 2.2 Cases & Audit Drill-Down Endpoints

#### `GET /api/cases`
Returns list of all active recovery cases with pagination and status filters.
- **Query Params:** `status` (optional), `failure_reason` (optional)
- **Response (200 OK):**
```json
[
  {
    "id": "att_001",
    "customer_id": "cust_001",
    "customer_name": "Rahul Sharma",
    "customer_phone": "+919876543210",
    "amount": 4999.0,
    "attempt_number": 1,
    "failure_reason": "insufficient_funds",
    "salary_credit_day": 1,
    "status": "pending",
    "scheduled_at": "2026-09-03T10:00:00Z",
    "next_action": "retry_scheduled",
    "decision_explanation": "Retry scheduled 2 days after salary day (1st)."
  }
]
```

#### `GET /api/cases/{attempt_id}/audit`
Retrieves the complete, chronological compliance audit trail for a single case.
- **Response (200 OK):**
```json
{
  "case_id": "att_001",
  "customer_name": "Rahul Sharma",
  "audit_trail": [
    {
      "id": "aud_01",
      "timestamp": "2026-09-01T10:00:00Z",
      "action": "retry_scheduled",
      "reasoning": "Initial mandate charge failed with insufficient_funds. Scheduled next retry on 2026-09-03 (Salary day 1 + 2d buffer).",
      "outcome": "pending",
      "amount_recovered": null
    }
  ]
}
```

---

### 2.3 Virtual Clock (Fast-Forward) Endpoints

#### `GET /api/clock`
Returns current simulated date and time.
- **Response (200 OK):**
```json
{
  "current_time": "2026-09-01T10:00:00Z"
}
```

#### `POST /api/clock/fast-forward`
Jumps the virtual clock forward by a specified number of days or hours, resolving pending retries and triggering grace nudges/escalations.
- **Request Body:**
```json
{
  "days": 2,
  "hours": 0
}
```
- **Response (200 OK):**
```json
{
  "previous_time": "2026-09-01T10:00:00Z",
  "new_time": "2026-09-03T10:00:00Z",
  "events_processed": [
    {
      "event_type": "retry_executed",
      "attempt_id": "att_001",
      "result": "success",
      "amount_recovered": 4999.0
    }
  ]
}
```

---

### 2.4 Conversational Promise-to-Pay (PTP) Chat Endpoints

#### `POST /api/chat/message`
Handles customer messages in the interactive chat drawer.
- **Request Body:**
```json
{
  "promise_id": "ptp_001",
  "message": "Agle somvar salary aayegi tab dunga pakka"
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "agent_reply": "Shukriya Rahul ji! Humne 2026-09-07 ka promise note kar liya hai. Payment link: https://rzp.io/l/rec_001",
  "extracted_data": {
    "has_commitment": true,
    "promised_date": "2026-09-07",
    "is_ambiguous": false
  },
  "promise_status": "open"
}
```

#### `GET /api/chat/{promise_id}/history`
Fetches all chat turns for a specific PTP negotiation.

---

### 2.5 Human Escalation Queue Endpoints

#### `GET /api/escalation/queue`
Fetches cases where all automated retries or grace nudges failed.
- **Response (200 OK):**
```json
[
  {
    "case_id": "att_015",
    "customer_name": "Sneha Reddy",
    "amount": 2499.0,
    "escalation_reason": "Broken promise followed by unanswered grace nudge.",
    "escalated_at": "2026-09-06T10:00:00Z",
    "status": "pending_human_review"
  }
]
```

---

## 3. Razorpay Integration & Webhook Handling

### Subscriptions & Webhooks
1. **Webhook Event `subscription.charged.failed`**:
   - Payload contains `mandate_id`, `error_code` (`BAD_REQUEST_INSUFFICIENT_FUNDS`, `BANK_TIMEOUT`, etc.).
   - Triggers the Decision Engine automatically.
2. **Webhook Event `payment_link.paid`**:
   - Payload contains `payment_link_id`, `amount_paid`.
   - Resolves active Promise-to-Pay status to `kept` and logs recovery.
