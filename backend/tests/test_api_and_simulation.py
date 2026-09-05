import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
# Import all models so Base.metadata is fully populated
from app.models import (
    Customer,
    MandateAttempt,
    PromiseToPay,
    ConversationLog,
    AuditLog,
    VirtualClock,
)

# Use in-memory SQLite with StaticPool for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_batch_run_and_summary():
    # 1. Trigger Batch Run
    res_run = client.post("/api/batch/run", json={"case_count": 15})
    assert res_run.status_code == 200
    data_run = res_run.json()
    assert data_run["status"] == "success"
    assert data_run["total_cases_loaded"] == 15
    assert data_run["summary"]["total_at_risk"] > 0

    # 2. Check Summary Metrics
    res_sum = client.get("/api/batch/summary")
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    assert data_sum["total_cases"] == 15
    assert data_sum["total_at_risk"] > 0


def test_cases_listing_and_audit():
    client.post("/api/batch/run", json={"case_count": 15})

    # List cases
    res_cases = client.get("/api/cases")
    assert res_cases.status_code == 200
    cases = res_cases.json()
    assert len(cases) == 15

    # Check audit trail of first case
    case_id = cases[0]["id"]
    res_audit = client.get(f"/api/cases/{case_id}/audit")
    assert res_audit.status_code == 200
    audit_trail = res_audit.json()
    assert len(audit_trail) >= 1
    assert "reasoning" in audit_trail[0]


def test_clock_fast_forward():
    client.post("/api/batch/run", json={"case_count": 15})

    # Advance clock by 2 days
    res_ff = client.post("/api/clock/fast-forward", json={"days": 2, "hours": 0})
    assert res_ff.status_code == 200
    data_ff = res_ff.json()
    assert data_ff["status"] == "success"
    assert data_ff["days_advanced"] == 2
    assert "events_processed" in data_ff


def test_chat_interaction():
    client.post("/api/batch/run", json={"case_count": 15})

    # Find a case routed to PTP
    res_cases = client.get("/api/cases")
    cases = res_cases.json()
    ptp_case = next((c for c in cases if c.get("active_promise_id")), None)
    assert ptp_case is not None

    promise_id = ptp_case["active_promise_id"]

    # Send ambiguous message
    res_chat1 = client.post(
        "/api/chat/message",
        json={"promise_id": promise_id, "message": "Jaldi dunga bhai"}
    )
    assert res_chat1.status_code == 200
    data1 = res_chat1.json()
    assert data1["extracted_data"]["is_ambiguous"] is True

    # Send definite date message
    res_chat2 = client.post(
        "/api/chat/message",
        json={"promise_id": promise_id, "message": "Agle Somvar pakka done"}
    )
    assert res_chat2.status_code == 200
    data2 = res_chat2.json()
    assert data2["extracted_data"]["has_commitment"] is True
    assert data2["payment_link"] is not None
