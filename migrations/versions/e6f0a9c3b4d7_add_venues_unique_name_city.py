"""add unique constraint on venues (name, city)

`venues` predates Alembic (see migrations/env.py) and was previously only
ever created via `Base.metadata.create_all` at application startup, so it
may or may not already exist when this migration runs: a fresh database
won't have it yet, while an already-running deployment will. Both cases are
handled here so the constraint ends up applied either way, matching the
`Venue` model (`src/models/venue.py`) exactly.

Revision ID: e6f0a9c3b4d7
Revises: a3f8c1d4e7b2
Create Date: 2026-10-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e6f0a9c3b4d7"
down_revision = "a3f8c1d4e7b2"
branch_labels = None
depends_on = None

_CONSTRAINT_NAME = "uq_venues_name_city"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "venues" not in inspector.get_table_names():
        op.create_table(
            "venues",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("city", sa.String(length=100), nullable=False),
            sa.Column("country", sa.String(length=100), nullable=False),
            sa.Column("capacity", sa.Integer(), nullable=True),
            sa.UniqueConstraint("name", "city", name=_CONSTRAINT_NAME),
        )
    else:
        with op.batch_alter_table("venues") as batch_op:
            batch_op.create_unique_constraint(_CONSTRAINT_NAME, ["name", "city"])


def downgrade() -> None:
    # Only ever drop the constraint, never the table itself: `venues`
    # normally predates this migration (see module docstring) and dropping
    # it on downgrade would destroy production data. In the rare case this
    # migration did create the table (a genuinely fresh, Alembic-only
    # database), leaving the now-unconstrained empty table behind is a
    # harmless no-op rather than a risky guess.
    with op.batch_alter_table("venues") as batch_op:
        batch_op.drop_constraint(_CONSTRAINT_NAME, type_="unique")
