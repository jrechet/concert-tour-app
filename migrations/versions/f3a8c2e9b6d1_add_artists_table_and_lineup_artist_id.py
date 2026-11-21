"""add artists table and lineup_entries.artist_id link

Revision ID: f3a8c2e9b6d1
Revises: 822d8600f5e7
Create Date: 2026-11-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f3a8c2e9b6d1"
down_revision = "822d8600f5e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_index("ix_artists_id", "artists", ["id"])

    op.add_column(
        "lineup_entries",
        sa.Column("artist_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_lineup_entries_artist_id", "lineup_entries", ["artist_id"])
    with op.batch_alter_table("lineup_entries") as batch_op:
        batch_op.create_foreign_key(
            "fk_lineup_entries_artist_id_artists", "artists", ["artist_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("lineup_entries") as batch_op:
        batch_op.drop_constraint("fk_lineup_entries_artist_id_artists", type_="foreignkey")
    op.drop_index("ix_lineup_entries_artist_id", table_name="lineup_entries")
    op.drop_column("lineup_entries", "artist_id")

    op.drop_index("ix_artists_id", table_name="artists")
    op.drop_table("artists")
