import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampSoftDeleteMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Leave(Base, TimestampSoftDeleteMixin):
    """
    Leave / permission request for an employee.
    Data model only — managed by future HR admin modules, not by end users.
    """

    __tablename__ = "leaves"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    leave_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # annual/sick/emergency/unpaid/maternity/paternity
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/approved/rejected
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="leaves")
