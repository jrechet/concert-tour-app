"""add lineup_entries table

Revision ID: b7f3a1c9d2e4
Revises:
Create Date: 2026-09-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7f3a1c9d2e4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lineup_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "concert_id",
            sa.Integer(),
            sa.ForeignKey("concerts.id"),
            nullable=False,
        ),
        sa.Column("artist_name", sa.String(length=200), nullable=False),
        sa.Column("set_order", sa.Integer(), nullable=False),
        sa.Column("set_time", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_lineup_entries_concert_id", "lineup_entries", ["concert_id"]
    )
    op.create_index(
        "ix_lineup_entries_concert_id_set_order",
        "lineup_entries",
        ["concert_id", "set_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_lineup_entries_concert_id_set_order", table_name="lineup_entries")
    op.drop_index("ix_lineup_entries_concert_id", table_name="lineup_entries")
    op.drop_table("lineup_entries")
