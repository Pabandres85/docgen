"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "batches",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="CREATED"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filename_pattern", sa.String(length=300), nullable=False, server_default="registro_{row_index}"),
        sa.Column("input_excel", sa.Text(), nullable=False, server_default=""),
        sa.Column("input_template", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_zip", sa.Text(), nullable=False, server_default=""),
        sa.Column("errors_csv", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "batch_items",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("batch_id", sa.String(length=32), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_pdf", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_batch_items_batch_id", "batch_items", ["batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_batch_items_batch_id", table_name="batch_items")
    op.drop_table("batch_items")
    op.drop_table("batches")
