import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EmployeeBase(BaseModel):
    name: str
    identity_number: Optional[str] = None
    identity_type: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    join_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_status: str = "active"
    salary: Optional[Decimal] = None
    salary_currency: str = "USD"
    emergency_contact: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    identity_number: Optional[str] = None
    identity_type: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    join_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_status: Optional[str] = None
    salary: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
