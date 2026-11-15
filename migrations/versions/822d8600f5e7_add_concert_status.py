"""add concert status column

Revision ID: 822d8600f5e7
Revises: c9d1e3f5a7b2
Create Date: 2026-11-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "822d8600f5e7"
down_revision = "c9d1e3f5a7b2"
branch_labels = None
depends_on = None

# Values must stay character-for-character identical to `ConcertStatus`
# (src/models/concert.py): "scheduled" and "cancelled", lowercase.
concert_status = sa.Enum("scheduled", "cancelled", name="concert_status", native_enum=False)


def upgrade() -> None:
    op.add_column(
        "concerts",
        sa.Column("status", concert_status, nullable=False, server_default="scheduled"),
    )
    op.execute("UPDATE concerts SET status = 'scheduled' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column("concerts", "status")
