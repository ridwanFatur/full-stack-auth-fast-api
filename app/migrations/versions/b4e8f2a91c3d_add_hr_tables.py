"""add hr tables

Revision ID: b4e8f2a91c3d
Revises: 3772ce949c9b
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e8f2a91c3d"
down_revision: Union[str, None] = "3772ce949c9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    #  companies                                                           #
    # ------------------------------------------------------------------ #
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("company_code", sa.String(length=50), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_type", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("tax_number", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("founded_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_user_id"), "companies", ["user_id"], unique=False)

    # ------------------------------------------------------------------ #
    #  employees                                                           #
    # ------------------------------------------------------------------ #
    op.create_table(
        "employees",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("identity_number", sa.String(length=100), nullable=True),
        sa.Column("identity_type", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("position", sa.String(length=100), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("join_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "employment_status",
            sa.String(length=30),
            nullable=False,
            server_default="active",
        ),
        sa.Column("salary", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column(
            "salary_currency", sa.String(length=10), nullable=False, server_default="USD"
        ),
        sa.Column("emergency_contact", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employees_company_id"), "employees", ["company_id"], unique=False
    )

    # ------------------------------------------------------------------ #
    #  attendances                                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        "attendances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check_in", sa.Time(), nullable=True),
        sa.Column("check_out", sa.Time(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="present"
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attendances_employee_id"), "attendances", ["employee_id"], unique=False
    )

    # ------------------------------------------------------------------ #
    #  leaves                                                              #
    # ------------------------------------------------------------------ #
    op.create_table(
        "leaves",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("leave_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_leaves_employee_id"), "leaves", ["employee_id"], unique=False
    )

    # ------------------------------------------------------------------ #
    #  payrolls                                                            #
    # ------------------------------------------------------------------ #
    op.create_table(
        "payrolls",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("base_salary", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("allowances", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("deductions", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("net_salary", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=10), nullable=False, server_default="USD"
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payrolls_employee_id"), "payrolls", ["employee_id"], unique=False
    )

    # ------------------------------------------------------------------ #
    #  performances                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "performances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("review_period", sa.String(length=50), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("goals", sa.Text(), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("areas_for_improvement", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_performances_employee_id"),
        "performances",
        ["employee_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_performances_employee_id"), table_name="performances")
    op.drop_table("performances")
    op.drop_index(op.f("ix_payrolls_employee_id"), table_name="payrolls")
    op.drop_table("payrolls")
    op.drop_index(op.f("ix_leaves_employee_id"), table_name="leaves")
    op.drop_table("leaves")
    op.drop_index(op.f("ix_attendances_employee_id"), table_name="attendances")
    op.drop_table("attendances")
    op.drop_index(op.f("ix_employees_company_id"), table_name="employees")
    op.drop_table("employees")
    op.drop_index(op.f("ix_companies_user_id"), table_name="companies")
    op.drop_table("companies")
