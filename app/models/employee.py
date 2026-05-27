import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampSoftDeleteMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.company import Company
    from app.models.leave import Leave
    from app.models.payroll import Payroll
    from app.models.performance import Performance


class Employee(Base, TimestampSoftDeleteMixin):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Personal info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    identity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # KTP, PASSPORT, etc.
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # male/female/other
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Job info
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    join_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # active/inactive/on_leave/terminated

    # Salary
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    salary_currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USD"
    )

    # Emergency contact
    emergency_contact: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="employees")
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="employee", lazy="select"
    )
    leaves: Mapped[List["Leave"]] = relationship(
        "Leave", back_populates="employee", lazy="select"
    )
    payrolls: Mapped[List["Payroll"]] = relationship(
        "Payroll", back_populates="employee", lazy="select"
    )
    performances: Mapped[List["Performance"]] = relationship(
        "Performance", back_populates="employee", lazy="select"
    )
