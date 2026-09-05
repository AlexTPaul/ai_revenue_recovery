from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas.batch import BatchRunRequest, BatchRunResponse, BatchSummaryResponse
from app.services.batch_runner import batch_runner_service
from app.services.clock_service import clock_service
from app.models.customer import Customer
from app.models.mandate import MandateAttempt
from app.models.promise import PromiseToPay
from app.models.audit import AuditLog

router = APIRouter(prefix="/batch", tags=["Batch Simulation"])


@router.post("/run", response_model=BatchRunResponse)
def run_batch(payload: BatchRunRequest = BatchRunRequest(), db: Session = Depends(get_db)):
    """Initializes and runs the pre-seeded simulation batch (default 15 cases)."""
    result = batch_runner_service.reset_and_seed_batch(db, case_count=payload.case_count)
    return BatchRunResponse(
        status="success",
        message=f"Successfully loaded and evaluated {result['total_cases_loaded']} recovery cases.",
        total_cases_loaded=result["total_cases_loaded"],
        simulated_date=result["simulated_date"],
        summary=result["summary"],
    )


@router.get("/summary", response_model=BatchSummaryResponse)
def get_batch_summary(db: Session = Depends(get_db)):
    """Returns top-level metric counters for the dashboard."""
    current_time = clock_service.get_current_time(db)

    # Total at risk (sum of unique initial mandate attempts)
    total_at_risk_query = (
        db.query(func.sum(MandateAttempt.amount))
        .filter(MandateAttempt.attempt_number == 1)
        .scalar()
    )
    total_at_risk = float(total_at_risk_query or 0.0)

    # Total recovered (from audit logs)
    total_recovered_query = (
        db.query(func.sum(AuditLog.amount_recovered))
        .filter(AuditLog.action == "recovered")
        .scalar()
    )
    total_recovered = float(total_recovered_query or 0.0)

    recovery_rate_pct = round((total_recovered / total_at_risk * 100), 2) if total_at_risk > 0 else 0.0

    total_cases = db.query(Customer).count()

    # Status breakdown
    pending_retries = db.query(MandateAttempt).filter(MandateAttempt.status == "pending").count()
    open_ptp = db.query(PromiseToPay).filter(PromiseToPay.status == "open").count()
    recovered_count = db.query(AuditLog).filter(AuditLog.action == "recovered").count()
    escalated_count = (
        db.query(AuditLog)
        .filter(AuditLog.action == "escalated")
        .count()
    )

    return BatchSummaryResponse(
        total_at_risk=total_at_risk,
        total_recovered=total_recovered,
        recovery_rate_pct=recovery_rate_pct,
        total_cases=total_cases,
        status_breakdown={
            "pending_retry": pending_retries,
            "ptp_open": open_ptp,
            "recovered": recovered_count,
            "escalated": escalated_count,
        },
        simulated_time=current_time.strftime("%Y-%m-%d %H:%M"),
    )


@router.post("/reset")
def reset_batch(db: Session = Depends(get_db)):
    """Resets the entire simulation to a clean blank state."""
    db.query(AuditLog).delete()
    db.query(PromiseToPay).delete()
    db.query(MandateAttempt).delete()
    db.query(Customer).delete()
    clock_service.reset_clock(db)
    db.commit()
    return {"status": "success", "message": "Simulation environment successfully reset."}
