import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class AttendanceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, attendance_id: uuid.UUID) -> Optional[Attendance]:
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.id == attendance_id, Attendance.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_employee(
        self, attendance_id: uuid.UUID, employee_id: uuid.UUID
    ) -> Optional[Attendance]:
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.id == attendance_id,
                Attendance.employee_id == employee_id,
                Attendance.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_employee(
        self, employee_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[Attendance], int]:
        base = select(Attendance).where(
            Attendance.employee_id == employee_id, Attendance.is_deleted == False
        )
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        items = (
            await self.db.execute(
                base.order_by(Attendance.date.desc()).offset(skip).limit(limit)
            )
        ).scalars().all()
        return items, total

    async def create(self, employee_id: uuid.UUID, data: AttendanceCreate) -> Attendance:
        obj = Attendance(employee_id=employee_id, **data.model_dump())
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Attendance, data: AttendanceUpdate) -> Attendance:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, obj: Attendance) -> None:
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
