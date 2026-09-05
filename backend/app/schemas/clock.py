from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel


class ClockStatusResponse(BaseModel):
    current_time: datetime
    formatted_time: str
    is_active: bool


class FastForwardRequest(BaseModel):
    days: int = 1
    hours: int = 0


class SimulationEvent(BaseModel):
    event_type: str
    entity_id: str
    description: str
    outcome: str
    amount_recovered: float = 0.0


class FastForwardResponse(BaseModel):
    status: str
    previous_time: datetime
    new_time: datetime
    days_advanced: int
    hours_advanced: int
    events_processed: List[SimulationEvent]
