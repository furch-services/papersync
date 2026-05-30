"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-05-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False, default=1),
        sa.Column("papierkram_api_url", sa.String(), nullable=False, server_default=""),
        sa.Column("papierkram_api_key_encrypted", sa.String(), nullable=False, server_default=""),
        sa.Column("paperless_base_url", sa.String(), nullable=False, server_default=""),
        sa.Column("paperless_api_token_encrypted", sa.String(), nullable=False, server_default=""),
        sa.Column("polling_interval_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("default_tags", sa.String(), nullable=True),
        sa.Column("default_document_type", sa.Integer(), nullable=True),
        sa.Column("default_correspondent", sa.Integer(), nullable=True),
        sa.Column("sync_non_draft_only", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "processed_documents",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("papierkram_document_id", sa.Integer(), nullable=False),
        sa.Column("paperless_document_id", sa.Integer(), nullable=True),
        sa.Column("paperless_task_uuid", sa.String(), nullable=True),
        sa.Column("invoice_no", sa.String(), nullable=True),
        sa.Column("document_date", sa.String(), nullable=True),
        sa.Column("total_gross", sa.Float(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("papierkram_document_id", name="uq_papierkram_document_id"),
    )
    op.create_index("idx_processed_papierkram_id", "processed_documents", ["papierkram_document_id"], unique=True)
    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer(), nullable=False, default=1),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_successful_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
        sa.Column("documents_synced_total", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sync_logs_timestamp", "sync_logs", ["timestamp"])
    op.create_index("idx_sync_logs_level", "sync_logs", ["level"])


def downgrade() -> None:
    op.drop_table("sync_logs")
    op.drop_table("sync_state")
    op.drop_table("processed_documents")
    op.drop_table("settings")
