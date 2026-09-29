"""add created_at column and unique constraint on lineup_entries

Revision ID: f1a2b3c4d5e6
Revises: d5e9f3a2b7c1
Create Date: 2026-09-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "d5e9f3a2b7c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lineup_entries",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    with op.batch_alter_table("lineup_entries") as batch_op:
        batch_op.create_unique_constraint(
            "uq_lineup_entries_concert_id_set_order", ["concert_id", "set_order"]
        )


def downgrade() -> None:
    with op.batch_alter_table("lineup_entries") as batch_op:
        batch_op.drop_constraint(
            "uq_lineup_entries_concert_id_set_order", type_="unique"
        )
    op.drop_column("lineup_entries", "created_at")
