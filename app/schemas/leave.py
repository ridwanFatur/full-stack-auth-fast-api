import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class LeaveBase(BaseModel):
    leave_type: str  # annual | sick | emergency | unpaid | maternity | paternity
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: str = "pending"  # pending | approved | rejected
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class LeaveResponse(LeaveBase):
    id: uuid.UUID
    employee_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeaveListResponse(BaseModel):
    items: list[LeaveResponse]
    total: int
