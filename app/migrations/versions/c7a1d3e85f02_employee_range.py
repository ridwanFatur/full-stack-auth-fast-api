"""replace employee_count with employee_range on companies

Revision ID: c7a1d3e85f02
Revises: b4e8f2a91c3d
Create Date: 2026-05-27 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7a1d3e85f02"
down_revision: Union[str, None] = "b4e8f2a91c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("employee_range", sa.String(length=20), nullable=True))
    op.drop_column("companies", "employee_count")


def downgrade() -> None:
    op.add_column("companies", sa.Column("employee_count", sa.Integer(), nullable=True))
    op.drop_column("companies", "employee_range")
