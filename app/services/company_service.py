import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.company_repository import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.storage_service import StorageService


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CompanyRepository(db)
        self.storage = StorageService()

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    async def list_companies(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> CompanyListResponse:
        items, total = await self.repo.list_by_user(user_id, skip=skip, limit=limit)
        return CompanyListResponse(
            items=[CompanyResponse.model_validate(c) for c in items],
            total=total,
        )

    async def get_company(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> CompanyResponse:
        company = await self.repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")
        return CompanyResponse.model_validate(company)

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    async def create_company(
        self, user_id: uuid.UUID, data: CompanyCreate
    ) -> CompanyResponse:
        company = await self.repo.create(user_id, data)
        return CompanyResponse.model_validate(company)

    async def update_company(
        self, company_id: uuid.UUID, user_id: uuid.UUID, data: CompanyUpdate
    ) -> CompanyResponse:
        company = await self.repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")
        company = await self.repo.update(company, data)
        return CompanyResponse.model_validate(company)

    async def delete_company(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        company = await self.repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")
        await self.repo.soft_delete(company)

    # ------------------------------------------------------------------ #
    #  Logo upload                                                         #
    # ------------------------------------------------------------------ #

    async def upload_logo(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> CompanyResponse:
        company = await self.repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")

        # Delete old logo if present (best-effort)
        if company.logo_url:
            await self.storage.delete_file(company.logo_url)

        logo_url = await self.storage.upload_file(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            folder="logos",
        )

        update_data = CompanyUpdate(logo_url=logo_url)
        company = await self.repo.update(company, update_data)
        return CompanyResponse.model_validate(company)
