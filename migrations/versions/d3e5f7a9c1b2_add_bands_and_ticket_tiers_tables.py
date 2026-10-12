"""add bands and ticket_tiers tables

Revision ID: d3e5f7a9c1b2
Revises: b2c6d8e1f3a5
Create Date: 2026-10-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d3e5f7a9c1b2"
down_revision = "b2c6d8e1f3a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("name", name="uq_bands_name"),
    )
    op.create_index("ix_bands_id", "bands", ["id"])

    op.create_table(
        "ticket_tiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "concert_id",
            sa.Integer(),
            sa.ForeignKey("concerts.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("concert_id", "name", name="uq_ticket_tiers_concert_id_name"),
    )
    op.create_index("ix_ticket_tiers_id", "ticket_tiers", ["id"])
    op.create_index("ix_ticket_tiers_concert_id", "ticket_tiers", ["concert_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_tiers_concert_id", table_name="ticket_tiers")
    op.drop_index("ix_ticket_tiers_id", table_name="ticket_tiers")
    op.drop_table("ticket_tiers")

    op.drop_index("ix_bands_id", table_name="bands")
    op.drop_table("bands")
