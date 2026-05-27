import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator


class CompanyBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    company_code: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    founded_at: Optional[date] = None
    status: str = "active"


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    company_code: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    tax_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    founded_at: Optional[date] = None
    status: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
