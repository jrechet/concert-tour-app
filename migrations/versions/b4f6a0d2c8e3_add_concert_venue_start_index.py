"""add composite index on concerts (venue_id, date_time)

Backs the venue-concerts listing endpoint (`GET /api/v1/venues/{id}/concerts`),
which filters on `venue_id` and orders by `date_time`, so that lookup stays
cheap as the `concerts` table grows.

The index is also declared on `Concert.__table_args__`, so `upgrade`/
`downgrade` use `if_not_exists`/`if_exists`: `concerts` is created via
`Base.metadata.create_all` at app startup (see `migrations/env.py`), not by
Alembic, so on a fresh database the index already exists by the time this
migration runs.

Revision ID: b4f6a0d2c8e3
Revises: a7c4e2f8b1d9
Create Date: 2026-11-11 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4f6a0d2c8e3"
down_revision = "a7c4e2f8b1d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_concerts_venue_id_date_time",
        "concerts",
        ["venue_id", "date_time"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_concerts_venue_id_date_time", table_name="concerts", if_exists=True)
