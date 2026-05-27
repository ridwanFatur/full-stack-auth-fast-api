import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import Payroll
from app.schemas.payroll import PayrollCreate, PayrollUpdate


class PayrollRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id_and_employee(
        self, payroll_id: uuid.UUID, employee_id: uuid.UUID
    ) -> Optional[Payroll]:
        result = await self.db.execute(
            select(Payroll).where(
                Payroll.id == payroll_id,
                Payroll.employee_id == employee_id,
                Payroll.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_employee(
        self, employee_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[Payroll], int]:
        base = select(Payroll).where(
            Payroll.employee_id == employee_id, Payroll.is_deleted == False
        )
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        items = (
            await self.db.execute(
                base.order_by(Payroll.period_start.desc()).offset(skip).limit(limit)
            )
        ).scalars().all()
        return items, total

    async def create(self, employee_id: uuid.UUID, net_salary, data: PayrollCreate) -> Payroll:
        obj = Payroll(
            employee_id=employee_id,
            net_salary=net_salary,
            **data.model_dump(),
        )
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Payroll, data: PayrollUpdate, net_salary=None) -> Payroll:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        if net_salary is not None:
            obj.net_salary = net_salary
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, obj: Payroll) -> None:
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
