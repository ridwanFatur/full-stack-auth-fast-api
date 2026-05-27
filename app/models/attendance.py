import uuid
from datetime import date, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampSoftDeleteMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Attendance(Base, TimestampSoftDeleteMixin):
    """
    Attendance record for an employee on a given date.
    Data model only — managed by future HR admin modules, not by end users.
    """

    __tablename__ = "attendances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="present"
    )  # present/absent/late/on_leave
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="attendances"
    )
