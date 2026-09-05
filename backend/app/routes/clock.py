from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.clock import (
    ClockStatusResponse,
    FastForwardRequest,
    FastForwardResponse,
)
from app.services.clock_service import clock_service

router = APIRouter(prefix="/clock", tags=["Virtual Clock Simulator"])


@router.get("", response_model=ClockStatusResponse)
def get_clock_status(db: Session = Depends(get_db)):
    """Fetches the current virtual simulation clock time."""
    clock = clock_service.get_or_create_clock(db)
    return ClockStatusResponse(
        current_time=clock.current_time,
        formatted_time=clock.current_time.strftime("%A, %d %B %Y, %I:%M %p"),
        is_active=clock.is_active,
    )


@router.post("/fast-forward", response_model=FastForwardResponse)
def fast_forward_time(payload: FastForwardRequest, db: Session = Depends(get_db)):
    """Advances the virtual simulation clock by N days/hours, processing scheduled events."""
    prev_time, new_time, events = clock_service.fast_forward(
        db, days=payload.days, hours=payload.hours
    )
    return FastForwardResponse(
        status="success",
        previous_time=prev_time,
        new_time=new_time,
        days_advanced=payload.days,
        hours_advanced=payload.hours,
        events_processed=events,
    )


@router.post("/reset", response_model=ClockStatusResponse)
def reset_clock(db: Session = Depends(get_db)):
    """Resets the virtual clock to the default start date (2026-09-01)."""
    clock = clock_service.reset_clock(db)
    return ClockStatusResponse(
        current_time=clock.current_time,
        formatted_time=clock.current_time.strftime("%A, %d %B %Y, %I:%M %p"),
        is_active=clock.is_active,
    )
