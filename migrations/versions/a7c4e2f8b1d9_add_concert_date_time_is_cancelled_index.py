"""add composite index on concerts (date_time, is_cancelled)

Speeds up the common "upcoming, non-cancelled concerts" queries (e.g.
`GET /api/v1/concerts/upcoming`, the sold-out listing, stats endpoints)
that filter on both columns together, on top of the existing single-column
`ix_concerts_date_time` index.

Revision ID: a7c4e2f8b1d9
Revises: d3e5f7a9c1b2
Create Date: 2026-10-18 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c4e2f8b1d9"
down_revision = "d3e5f7a9c1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_concerts_date_time_is_cancelled",
        "concerts",
        ["date_time", "is_cancelled"],
    )


def downgrade() -> None:
    op.drop_index("ix_concerts_date_time_is_cancelled", table_name="concerts")
