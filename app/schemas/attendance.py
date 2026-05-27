import uuid
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel


class AttendanceBase(BaseModel):
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "present"  # present | absent | late | on_leave | wfh
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    date: Optional[date] = None
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: uuid.UUID
    employee_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttendanceListResponse(BaseModel):
    items: list[AttendanceResponse]
    total: int
