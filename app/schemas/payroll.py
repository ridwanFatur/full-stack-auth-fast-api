import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class PayrollBase(BaseModel):
    period_start: date
    period_end: date
    base_salary: Decimal
    allowances: Optional[Decimal] = Decimal("0")
    deductions: Optional[Decimal] = Decimal("0")
    net_salary: Decimal
    currency: str = "USD"
    status: str = "pending"  # pending | processed | paid
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None


class PayrollCreate(BaseModel):
    period_start: date
    period_end: date
    base_salary: Decimal
    allowances: Optional[Decimal] = Decimal("0")
    deductions: Optional[Decimal] = Decimal("0")
    currency: str = "USD"
    status: str = "pending"
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None

    @property
    def computed_net_salary(self) -> Decimal:
        return (self.base_salary or Decimal("0")) + (self.allowances or Decimal("0")) - (self.deductions or Decimal("0"))


class PayrollUpdate(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    base_salary: Optional[Decimal] = None
    allowances: Optional[Decimal] = None
    deductions: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None


class PayrollResponse(PayrollBase):
    id: uuid.UUID
    employee_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PayrollListResponse(BaseModel):
    items: list[PayrollResponse]
    total: int
