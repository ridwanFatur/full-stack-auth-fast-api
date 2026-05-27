import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.company_repository import CompanyRepository
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.storage_service import StorageService


class EmployeeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = EmployeeRepository(db)
        self.company_repo = CompanyRepository(db)
        self.storage = StorageService()

    # ------------------------------------------------------------------ #
    #  Ownership guard                                                     #
    # ------------------------------------------------------------------ #

    async def _assert_company_owned(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        company = await self.company_repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    async def list_employees(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> EmployeeListResponse:
        await self._assert_company_owned(company_id, user_id)
        items, total = await self.repo.list_by_company(company_id, skip=skip, limit=limit)
        return EmployeeListResponse(
            items=[EmployeeResponse.model_validate(e) for e in items],
            total=total,
        )

    async def get_employee(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID
    ) -> EmployeeResponse:
        await self._assert_company_owned(company_id, user_id)
        employee = await self.repo.get_by_id_and_company(employee_id, company_id)
        if not employee:
            raise ValueError("Employee not found.")
        return EmployeeResponse.model_validate(employee)

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    async def create_employee(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        data: EmployeeCreate,
    ) -> EmployeeResponse:
        await self._assert_company_owned(company_id, user_id)
        employee = await self.repo.create(company_id, data)
        return EmployeeResponse.model_validate(employee)

    async def update_employee(
        self,
        company_id: uuid.UUID,
        employee_id: uuid.UUID,
        user_id: uuid.UUID,
        data: EmployeeUpdate,
    ) -> EmployeeResponse:
        await self._assert_company_owned(company_id, user_id)
        employee = await self.repo.get_by_id_and_company(employee_id, company_id)
        if not employee:
            raise ValueError("Employee not found.")
        employee = await self.repo.update(employee, data)
        return EmployeeResponse.model_validate(employee)

    async def delete_employee(
        self,
        company_id: uuid.UUID,
        employee_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._assert_company_owned(company_id, user_id)
        employee = await self.repo.get_by_id_and_company(employee_id, company_id)
        if not employee:
            raise ValueError("Employee not found.")
        await self.repo.soft_delete(employee)

    # ------------------------------------------------------------------ #
    #  Photo upload                                                        #
    # ------------------------------------------------------------------ #

    async def upload_photo(
        self,
        company_id: uuid.UUID,
        employee_id: uuid.UUID,
        user_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> EmployeeResponse:
        await self._assert_company_owned(company_id, user_id)
        employee = await self.repo.get_by_id_and_company(employee_id, company_id)
        if not employee:
            raise ValueError("Employee not found.")

        if employee.photo_url:
            await self.storage.delete_file(employee.photo_url)

        photo_url = await self.storage.upload_file(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            folder="employee-photos",
        )

        update_data = EmployeeUpdate(photo_url=photo_url)
        employee = await self.repo.update(employee, update_data)
        return EmployeeResponse.model_validate(employee)
