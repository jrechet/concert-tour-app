"""add unique constraint on artists.name

Any artist rows sharing a name are merged before the constraint is added
so `upgrade()` cannot fail mid-flight on pre-existing duplicate data: for
each duplicate name, every `lineup_entries.artist_id` pointing at a
duplicate is repointed to the lowest-id survivor, and the duplicate
`artists` rows are then deleted. Matches `Artist` (`src/models/artist.py`)
exactly, including the constraint name (`uq_artists_name`) and the
case-sensitive comparison on `name`.

Revision ID: 2fa2316309a8
Revises: f3a8c2e9b6d1
Create Date: 2026-11-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2fa2316309a8"
down_revision = "f3a8c2e9b6d1"
branch_labels = None
depends_on = None

_CONSTRAINT_NAME = "uq_artists_name"


def _dedupe_artist_names(bind) -> None:
    """Merge any `artists` rows sharing a name onto one surviving row."""
    rows = bind.execute(sa.text("SELECT id, name FROM artists ORDER BY id")).fetchall()

    survivor_by_name = {}
    duplicate_to_survivor = {}
    for artist_id, name in rows:
        if name in survivor_by_name:
            duplicate_to_survivor[artist_id] = survivor_by_name[name]
        else:
            survivor_by_name[name] = artist_id

    for duplicate_id, survivor_id in duplicate_to_survivor.items():
        bind.execute(
            sa.text("UPDATE lineup_entries SET artist_id = :survivor_id WHERE artist_id = :duplicate_id"),
            {"survivor_id": survivor_id, "duplicate_id": duplicate_id},
        )
        bind.execute(sa.text("DELETE FROM artists WHERE id = :duplicate_id"), {"duplicate_id": duplicate_id})


def upgrade() -> None:
    bind = op.get_bind()
    _dedupe_artist_names(bind)

    with op.batch_alter_table("artists") as batch_op:
        batch_op.create_unique_constraint(_CONSTRAINT_NAME, ["name"])


def downgrade() -> None:
    with op.batch_alter_table("artists") as batch_op:
        batch_op.drop_constraint(_CONSTRAINT_NAME, type_="unique")
