import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, company_id: uuid.UUID) -> Optional[Company]:
        result = await self.db.execute(
            select(Company).where(
                Company.id == company_id, Company.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Company]:
        """Return company only if it belongs to the given user."""
        result = await self.db.execute(
            select(Company).where(
                Company.id == company_id,
                Company.user_id == user_id,
                Company.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Company], int]:
        base_query = select(Company).where(
            Company.user_id == user_id, Company.is_deleted == False
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total: int = count_result.scalar_one()

        result = await self.db.execute(
            base_query.order_by(Company.created_at.desc()).offset(skip).limit(limit)
        )
        items = result.scalars().all()

        return items, total

    async def create(self, user_id: uuid.UUID, data: CompanyCreate) -> Company:
        company = Company(user_id=user_id, **data.model_dump())
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def update(self, company: Company, data: CompanyUpdate) -> Company:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def soft_delete(self, company: Company) -> None:
        from datetime import datetime, timezone

        company.is_deleted = True
        company.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
