"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2023-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create venues table
    op.create_table('venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_venues_id'), 'venues', ['id'], unique=False)

    # Create tours table
    op.create_table('tours',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('PLANNING', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='tourstatus'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tours_id'), 'tours', ['id'], unique=False)

    # Create concerts table
    op.create_table('concerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tour_id', sa.Integer(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('ticket_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'SOLD_OUT', 'CANCELLED', 'COMPLETED', name='concertstatus'), nullable=False),
        sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_concerts_id'), 'concerts', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_concerts_id'), table_name='concerts')
    op.drop_table('concerts')
    op.drop_index(op.f('ix_tours_id'), table_name='tours')
    op.drop_table('tours')
    op.drop_index(op.f('ix_venues_id'), table_name='venues')
    op.drop_table('venues')
