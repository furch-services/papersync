"""Add status and retry_count to processed_documents

Revision ID: 002
Revises: 001
Create Date: 2026-06-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processed_documents",
        sa.Column("status", sa.String(length=16), nullable=False, server_default="UPLOADED"),
    )
    op.add_column(
        "processed_documents",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("processed_documents", "retry_count")
    op.drop_column("processed_documents", "status")
