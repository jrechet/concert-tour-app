"""add concert cancellation fields

Revision ID: c4d8e2f1a6b3
Revises: b7f3a1c9d2e4
Create Date: 2026-09-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c4d8e2f1a6b3"
down_revision = "b7f3a1c9d2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "concerts",
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "concerts",
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("concerts", "cancellation_reason")
    op.drop_column("concerts", "is_cancelled")
