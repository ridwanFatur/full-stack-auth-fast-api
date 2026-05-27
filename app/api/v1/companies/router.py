"""
Companies & Employees API
-------------------------
/api/v1/companies                                                  — company CRUD
/api/v1/companies/{id}/logo                                        — logo upload
/api/v1/companies/{id}/employees                                   — employee CRUD
/api/v1/companies/{id}/employees/{eid}/photo                       — employee photo upload
/api/v1/companies/{id}/employees/{eid}/attendances                 — attendance CRUD
/api/v1/companies/{id}/employees/{eid}/leaves                      — leave CRUD
/api/v1/companies/{id}/employees/{eid}/payrolls                    — payroll CRUD
/api/v1/companies/{id}/employees/{eid}/performances                — performance CRUD
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceUpdate,
)
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
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
from app.services.company_service import CompanyService
from app.services.employee_service import EmployeeService
from app.services.hr_service import HRService

router = APIRouter(prefix="/companies", tags=["companies"])

# ====================================================================== #
#  Companies                                                               #
# ====================================================================== #


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyListResponse:
    """List all companies owned by the authenticated user."""
    service = CompanyService(db)
    return await service.list_companies(current_user.id, skip=skip, limit=limit)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyResponse:
    """Create a new company for the authenticated user."""
    service = CompanyService(db)
    return await service.create_company(current_user.id, data)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyResponse:
    """Get a company by ID (must belong to the authenticated user)."""
    service = CompanyService(db)
    try:
        return await service.get_company(company_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyResponse:
    """Update a company (must belong to the authenticated user)."""
    service = CompanyService(db)
    try:
        return await service.update_company(company_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-delete a company (must belong to the authenticated user)."""
    service = CompanyService(db)
    try:
        await service.delete_company(company_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{company_id}/logo", response_model=CompanyResponse)
async def upload_company_logo(
    company_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyResponse:
    """Upload or replace the company logo. Stores in Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted for the logo.",
        )
    service = CompanyService(db)
    try:
        file_bytes = await file.read()
        return await service.upload_logo(
            company_id=company_id,
            user_id=current_user.id,
            file_bytes=file_bytes,
            filename=file.filename or "logo",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValueError, ImportError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# ====================================================================== #
#  Employees (nested under /companies/{id}/employees)                     #
# ====================================================================== #


@router.get("/{company_id}/employees", response_model=EmployeeListResponse)
async def list_employees(
    company_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeListResponse:
    """List all employees in a company (company must belong to the authenticated user)."""
    service = EmployeeService(db)
    try:
        return await service.list_employees(company_id, current_user.id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    company_id: uuid.UUID,
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeResponse:
    """Add a new employee to a company."""
    service = EmployeeService(db)
    try:
        return await service.create_employee(company_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{company_id}/employees/{employee_id}", response_model=EmployeeResponse
)
async def get_employee(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeResponse:
    """Get an employee by ID."""
    service = EmployeeService(db)
    try:
        return await service.get_employee(company_id, employee_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{company_id}/employees/{employee_id}", response_model=EmployeeResponse
)
async def update_employee(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeResponse:
    """Update an employee."""
    service = EmployeeService(db)
    try:
        return await service.update_employee(company_id, employee_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{company_id}/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-delete an employee."""
    service = EmployeeService(db)
    try:
        await service.delete_employee(company_id, employee_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees/{employee_id}/photo",
    response_model=EmployeeResponse,
)
async def upload_employee_photo(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployeeResponse:
    """Upload or replace an employee's profile photo. Stores in Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted for the photo.",
        )
    service = EmployeeService(db)
    try:
        file_bytes = await file.read()
        return await service.upload_photo(
            company_id=company_id,
            employee_id=employee_id,
            user_id=current_user.id,
            file_bytes=file_bytes,
            filename=file.filename or "photo",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValueError, ImportError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# ====================================================================== #
#  Attendance                                                              #
# ====================================================================== #


@router.get(
    "/{company_id}/employees/{employee_id}/attendances",
    response_model=AttendanceListResponse,
)
async def list_attendance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceListResponse:
    service = HRService(db)
    try:
        return await service.list_attendance(company_id, employee_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees/{employee_id}/attendances",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_attendance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceResponse:
    service = HRService(db)
    try:
        return await service.create_attendance(company_id, employee_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{company_id}/employees/{employee_id}/attendances/{attendance_id}",
    response_model=AttendanceResponse,
)
async def update_attendance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    attendance_id: uuid.UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceResponse:
    service = HRService(db)
    try:
        return await service.update_attendance(company_id, employee_id, attendance_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{company_id}/employees/{employee_id}/attendances/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attendance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    attendance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = HRService(db)
    try:
        await service.delete_attendance(company_id, employee_id, attendance_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ====================================================================== #
#  Leave                                                                   #
# ====================================================================== #


@router.get(
    "/{company_id}/employees/{employee_id}/leaves",
    response_model=LeaveListResponse,
)
async def list_leave(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveListResponse:
    service = HRService(db)
    try:
        return await service.list_leave(company_id, employee_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees/{employee_id}/leaves",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: LeaveCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveResponse:
    service = HRService(db)
    try:
        return await service.create_leave(company_id, employee_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{company_id}/employees/{employee_id}/leaves/{leave_id}",
    response_model=LeaveResponse,
)
async def update_leave(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    leave_id: uuid.UUID,
    data: LeaveUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveResponse:
    service = HRService(db)
    try:
        return await service.update_leave(company_id, employee_id, leave_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{company_id}/employees/{employee_id}/leaves/{leave_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_leave(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    leave_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = HRService(db)
    try:
        await service.delete_leave(company_id, employee_id, leave_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ====================================================================== #
#  Payroll                                                                 #
# ====================================================================== #


@router.get(
    "/{company_id}/employees/{employee_id}/payrolls",
    response_model=PayrollListResponse,
)
async def list_payroll(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PayrollListResponse:
    service = HRService(db)
    try:
        return await service.list_payroll(company_id, employee_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees/{employee_id}/payrolls",
    response_model=PayrollResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payroll(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: PayrollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PayrollResponse:
    service = HRService(db)
    try:
        return await service.create_payroll(company_id, employee_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{company_id}/employees/{employee_id}/payrolls/{payroll_id}",
    response_model=PayrollResponse,
)
async def update_payroll(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    payroll_id: uuid.UUID,
    data: PayrollUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PayrollResponse:
    service = HRService(db)
    try:
        return await service.update_payroll(company_id, employee_id, payroll_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{company_id}/employees/{employee_id}/payrolls/{payroll_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_payroll(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    payroll_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = HRService(db)
    try:
        await service.delete_payroll(company_id, employee_id, payroll_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ====================================================================== #
#  Performance                                                             #
# ====================================================================== #


@router.get(
    "/{company_id}/employees/{employee_id}/performances",
    response_model=PerformanceListResponse,
)
async def list_performance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PerformanceListResponse:
    service = HRService(db)
    try:
        return await service.list_performance(company_id, employee_id, current_user.id, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{company_id}/employees/{employee_id}/performances",
    response_model=PerformanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: PerformanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PerformanceResponse:
    service = HRService(db)
    try:
        return await service.create_performance(company_id, employee_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{company_id}/employees/{employee_id}/performances/{performance_id}",
    response_model=PerformanceResponse,
)
async def update_performance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    performance_id: uuid.UUID,
    data: PerformanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PerformanceResponse:
    service = HRService(db)
    try:
        return await service.update_performance(
            company_id, employee_id, performance_id, current_user.id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{company_id}/employees/{employee_id}/performances/{performance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_performance(
    company_id: uuid.UUID,
    employee_id: uuid.UUID,
    performance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = HRService(db)
    try:
        await service.delete_performance(
            company_id, employee_id, performance_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
