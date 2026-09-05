from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean

from app.database import Base


class VirtualClock(Base):
    __tablename__ = "virtual_clock"

    id = Column(Integer, primary_key=True, default=1)
    current_time = Column(DateTime, default=lambda: datetime(2026, 9, 1, 10, 0, 0), nullable=False)
    is_active = Column(Boolean, default=True)
