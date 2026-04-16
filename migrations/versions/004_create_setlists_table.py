"""Create setlists table

Revision ID: 004
Revises: 003
Create Date: 2024-12-28 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'setlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('concert_id', sa.Integer(), nullable=False),
        sa.Column('song_id', sa.Integer(), nullable=False),
        sa.Column('order_position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['concert_id'], ['concerts.id'], ),
        sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_setlists_id'), 'setlists', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_setlists_id'), table_name='setlists')
    op.drop_table('setlists')
