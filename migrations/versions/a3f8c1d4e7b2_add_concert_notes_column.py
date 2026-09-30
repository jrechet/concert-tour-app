"""add concert notes column

Revision ID: a3f8c1d4e7b2
Revises: f1a2b3c4d5e6
Create Date: 2026-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3f8c1d4e7b2"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "concerts",
        sa.Column("notes", sa.String(length=500), nullable=True, server_default=None),
    )


def downgrade() -> None:
    op.drop_column("concerts", "notes")
