from typing import Optional, Dict
from pydantic import BaseModel


class BatchRunRequest(BaseModel):
    case_count: int = 15


class BatchRunResponse(BaseModel):
    status: str
    message: str
    total_cases_loaded: int
    simulated_date: str
    summary: Dict[str, float | int]


class BatchSummaryResponse(BaseModel):
    total_at_risk: float
    total_recovered: float
    recovery_rate_pct: float
    total_cases: int
    status_breakdown: Dict[str, int]
    simulated_time: str
