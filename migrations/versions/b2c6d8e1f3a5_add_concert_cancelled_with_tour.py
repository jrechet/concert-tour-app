"""add concert cancelled_with_tour column

Revision ID: b2c6d8e1f3a5
Revises: e6f0a9c3b4d7
Create Date: 2026-10-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c6d8e1f3a5"
down_revision = "e6f0a9c3b4d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "concerts",
        sa.Column("cancelled_with_tour", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.execute("UPDATE concerts SET cancelled_with_tour = 0")


def downgrade() -> None:
    op.drop_column("concerts", "cancelled_with_tour")
