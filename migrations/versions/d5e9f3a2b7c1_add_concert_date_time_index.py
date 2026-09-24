"""add index on concerts.date_time for chronological sort performance

Revision ID: d5e9f3a2b7c1
Revises: c4d8e2f1a6b3
Create Date: 2026-09-24 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d5e9f3a2b7c1"
down_revision = "c4d8e2f1a6b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_concerts_date_time", "concerts", ["date_time"])


def downgrade() -> None:
    op.drop_index("ix_concerts_date_time", table_name="concerts")
