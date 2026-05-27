import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PerformanceBase(BaseModel):
    review_period: str  # e.g. "2024-Q1", "2024-Annual"
    rating: Optional[float] = None  # 1.0–5.0
    goals: Optional[str] = None
    achievements: Optional[str] = None
    feedback: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    reviewer: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    status: str = "pending"  # pending | completed


class PerformanceCreate(PerformanceBase):
    pass


class PerformanceUpdate(BaseModel):
    review_period: Optional[str] = None
    rating: Optional[float] = None
    goals: Optional[str] = None
    achievements: Optional[str] = None
    feedback: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    reviewer: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    status: Optional[str] = None


class PerformanceResponse(PerformanceBase):
    id: uuid.UUID
    employee_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PerformanceListResponse(BaseModel):
    items: list[PerformanceResponse]
    total: int
