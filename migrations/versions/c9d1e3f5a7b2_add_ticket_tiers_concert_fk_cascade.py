"""add ondelete=CASCADE to ticket_tiers.concert_id foreign key

Revision ID: c9d1e3f5a7b2
Revises: b4f6a0d2c8e3
Create Date: 2026-11-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c9d1e3f5a7b2"
down_revision = "b4f6a0d2c8e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table(
        "ticket_tiers",
        recreate="always",
        copy_from=sa.Table(
            "ticket_tiers",
            sa.MetaData(),
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "concert_id",
                sa.Integer(),
                sa.ForeignKey("concerts.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.UniqueConstraint("concert_id", "name", name="uq_ticket_tiers_concert_id_name"),
        ),
    ):
        pass
    op.create_index("ix_ticket_tiers_id", "ticket_tiers", ["id"])
    op.create_index("ix_ticket_tiers_concert_id", "ticket_tiers", ["concert_id"])


def downgrade() -> None:
    with op.batch_alter_table(
        "ticket_tiers",
        recreate="always",
        copy_from=sa.Table(
            "ticket_tiers",
            sa.MetaData(),
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
        ),
    ):
        pass
    op.create_index("ix_ticket_tiers_id", "ticket_tiers", ["id"])
    op.create_index("ix_ticket_tiers_concert_id", "ticket_tiers", ["concert_id"])
