"""
HRService — manages Attendance, Leave, Payroll, and Performance records.

Ownership is enforced: every write verifies the company belongs to the
requesting user before touching employee records.
"""
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.leave_repository import LeaveRepository
from app.repositories.payroll_repository import PayrollRepository
from app.repositories.performance_repository import PerformanceRepository
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceUpdate,
)
from app.schemas.leave import (
    LeaveCreate,
    LeaveListResponse,
    LeaveResponse,
    LeaveUpdate,
)
from app.schemas.payroll import (
    PayrollCreate,
    PayrollListResponse,
    PayrollResponse,
    PayrollUpdate,
)
from app.schemas.performance import (
    PerformanceCreate,
    PerformanceListResponse,
    PerformanceResponse,
    PerformanceUpdate,
)


class HRService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.leave_repo = LeaveRepository(db)
        self.payroll_repo = PayrollRepository(db)
        self.performance_repo = PerformanceRepository(db)

    # ------------------------------------------------------------------ #
    #  Guard helpers                                                       #
    # ------------------------------------------------------------------ #

    async def _assert_employee_access(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        company = await self.company_repo.get_by_id_and_user(company_id, user_id)
        if not company:
            raise ValueError("Company not found or access denied.")
        employee = await self.employee_repo.get_by_id_and_company(employee_id, company_id)
        if not employee:
            raise ValueError("Employee not found.")

    # ================================================================== #
    #  Attendance                                                          #
    # ================================================================== #

    async def list_attendance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
    ) -> AttendanceListResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        items, total = await self.attendance_repo.list_by_employee(employee_id, skip, limit)
        return AttendanceListResponse(
            items=[AttendanceResponse.model_validate(i) for i in items], total=total
        )

    async def create_attendance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        data: AttendanceCreate,
    ) -> AttendanceResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.attendance_repo.create(employee_id, data)
        return AttendanceResponse.model_validate(obj)

    async def update_attendance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, attendance_id: uuid.UUID,
        user_id: uuid.UUID, data: AttendanceUpdate,
    ) -> AttendanceResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.attendance_repo.get_by_id_and_employee(attendance_id, employee_id)
        if not obj:
            raise ValueError("Attendance record not found.")
        obj = await self.attendance_repo.update(obj, data)
        return AttendanceResponse.model_validate(obj)

    async def delete_attendance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, attendance_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.attendance_repo.get_by_id_and_employee(attendance_id, employee_id)
        if not obj:
            raise ValueError("Attendance record not found.")
        await self.attendance_repo.soft_delete(obj)

    # ================================================================== #
    #  Leave                                                               #
    # ================================================================== #

    async def list_leave(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
    ) -> LeaveListResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        items, total = await self.leave_repo.list_by_employee(employee_id, skip, limit)
        return LeaveListResponse(
            items=[LeaveResponse.model_validate(i) for i in items], total=total
        )

    async def create_leave(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        data: LeaveCreate,
    ) -> LeaveResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.leave_repo.create(employee_id, data)
        return LeaveResponse.model_validate(obj)

    async def update_leave(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, leave_id: uuid.UUID,
        user_id: uuid.UUID, data: LeaveUpdate,
    ) -> LeaveResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.leave_repo.get_by_id_and_employee(leave_id, employee_id)
        if not obj:
            raise ValueError("Leave record not found.")
        obj = await self.leave_repo.update(obj, data)
        return LeaveResponse.model_validate(obj)

    async def delete_leave(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, leave_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.leave_repo.get_by_id_and_employee(leave_id, employee_id)
        if not obj:
            raise ValueError("Leave record not found.")
        await self.leave_repo.soft_delete(obj)

    # ================================================================== #
    #  Payroll                                                             #
    # ================================================================== #

    async def list_payroll(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
    ) -> PayrollListResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        items, total = await self.payroll_repo.list_by_employee(employee_id, skip, limit)
        return PayrollListResponse(
            items=[PayrollResponse.model_validate(i) for i in items], total=total
        )

    async def create_payroll(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        data: PayrollCreate,
    ) -> PayrollResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        net = data.computed_net_salary
        obj = await self.payroll_repo.create(employee_id, net, data)
        return PayrollResponse.model_validate(obj)

    async def update_payroll(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, payroll_id: uuid.UUID,
        user_id: uuid.UUID, data: PayrollUpdate,
    ) -> PayrollResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.payroll_repo.get_by_id_and_employee(payroll_id, employee_id)
        if not obj:
            raise ValueError("Payroll record not found.")
        # Recalculate net if salary components changed
        base = data.base_salary if data.base_salary is not None else obj.base_salary
        allowances = data.allowances if data.allowances is not None else (obj.allowances or Decimal("0"))
        deductions = data.deductions if data.deductions is not None else (obj.deductions or Decimal("0"))
        net = base + allowances - deductions
        obj = await self.payroll_repo.update(obj, data, net_salary=net)
        return PayrollResponse.model_validate(obj)

    async def delete_payroll(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, payroll_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.payroll_repo.get_by_id_and_employee(payroll_id, employee_id)
        if not obj:
            raise ValueError("Payroll record not found.")
        await self.payroll_repo.soft_delete(obj)

    # ================================================================== #
    #  Performance                                                         #
    # ================================================================== #

    async def list_performance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
    ) -> PerformanceListResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        items, total = await self.performance_repo.list_by_employee(employee_id, skip, limit)
        return PerformanceListResponse(
            items=[PerformanceResponse.model_validate(i) for i in items], total=total
        )

    async def create_performance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, user_id: uuid.UUID,
        data: PerformanceCreate,
    ) -> PerformanceResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.performance_repo.create(employee_id, data)
        return PerformanceResponse.model_validate(obj)

    async def update_performance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, performance_id: uuid.UUID,
        user_id: uuid.UUID, data: PerformanceUpdate,
    ) -> PerformanceResponse:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.performance_repo.get_by_id_and_employee(performance_id, employee_id)
        if not obj:
            raise ValueError("Performance record not found.")
        obj = await self.performance_repo.update(obj, data)
        return PerformanceResponse.model_validate(obj)

    async def delete_performance(
        self, company_id: uuid.UUID, employee_id: uuid.UUID, performance_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        await self._assert_employee_access(company_id, employee_id, user_id)
        obj = await self.performance_repo.get_by_id_and_employee(performance_id, employee_id)
        if not obj:
            raise ValueError("Performance record not found.")
        await self.performance_repo.soft_delete(obj)
