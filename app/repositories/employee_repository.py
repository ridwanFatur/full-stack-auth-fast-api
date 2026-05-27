import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, employee_id: uuid.UUID) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(
                Employee.id == employee_id, Employee.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_company(
        self, employee_id: uuid.UUID, company_id: uuid.UUID
    ) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.company_id == company_id,
                Employee.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Employee], int]:
        base_query = select(Employee).where(
            Employee.company_id == company_id, Employee.is_deleted == False
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total: int = count_result.scalar_one()

        result = await self.db.execute(
            base_query.order_by(Employee.created_at.desc()).offset(skip).limit(limit)
        )
        items = result.scalars().all()

        return items, total

    async def create(self, company_id: uuid.UUID, data: EmployeeCreate) -> Employee:
        employee = Employee(company_id=company_id, **data.model_dump())
        self.db.add(employee)
        await self.db.flush()
        await self.db.refresh(employee)
        return employee

    async def update(self, employee: Employee, data: EmployeeUpdate) -> Employee:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(employee, field, value)
        await self.db.flush()
        await self.db.refresh(employee)
        return employee

    async def soft_delete(self, employee: Employee) -> None:
        from datetime import datetime, timezone

        employee.is_deleted = True
        employee.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
