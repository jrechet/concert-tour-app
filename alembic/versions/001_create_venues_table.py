"""create venues table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create venues table
    op.create_table(
        'venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('stage_size', sa.String(length=100), nullable=True),
        sa.Column('sound_system', sa.String(length=200), nullable=True),
        sa.Column('lighting_rig', sa.String(length=200), nullable=True),
        sa.Column('contact_name', sa.String(length=100), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_venues_id'), 'venues', ['id'], unique=False)
    op.create_index(op.f('ix_venues_name'), 'venues', ['name'], unique=False)
    op.create_index(op.f('ix_venues_city'), 'venues', ['city'], unique=False)
    op.create_index(op.f('ix_venues_country'), 'venues', ['country'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_venues_country'), table_name='venues')
    op.drop_index(op.f('ix_venues_city'), table_name='venues')
    op.drop_index(op.f('ix_venues_name'), table_name='venues')
    op.drop_index(op.f('ix_venues_id'), table_name='venues')
    
    # Drop table
    op.drop_table('venues')
