"""add concert capacity column

Revision ID: 9b1e4f7a2c6d
Revises: 2fa2316309a8
Create Date: 2026-11-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9b1e4f7a2c6d"
down_revision = "2fa2316309a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "concerts",
        sa.Column("capacity", sa.Integer(), nullable=True, server_default=None),
    )


def downgrade() -> None:
    op.drop_column("concerts", "capacity")
