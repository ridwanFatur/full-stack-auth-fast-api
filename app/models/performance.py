import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampSoftDeleteMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Performance(Base, TimestampSoftDeleteMixin):
    """
    Performance review record for an employee.
    Data model only — managed by future HR admin modules, not by end users.
    """

    __tablename__ = "performances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_period: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. "2024-Q1", "2024-Annual"
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0–5.0
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    areas_for_improvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/completed

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="performances"
    )
