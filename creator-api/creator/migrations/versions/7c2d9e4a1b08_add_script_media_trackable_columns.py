"""add_script_media_trackable_columns

Revision ID: 7c2d9e4a1b08
Revises: 3f8a92b1c045
Create Date: 2026-06-01 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '7c2d9e4a1b08'
down_revision = '3f8a92b1c045'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'script_media',
        sa.Column('created_by', sa.BigInteger(), nullable=True),
    )
    op.add_column(
        'script_media',
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        'fk_script_media_created_by_bo_users',
        'script_media',
        'bo_users',
        ['created_by'],
        ['id'],
    )
    op.create_foreign_key(
        'fk_script_media_updated_by_bo_users',
        'script_media',
        'bo_users',
        ['updated_by'],
        ['id'],
    )


def downgrade():
    op.drop_constraint('fk_script_media_updated_by_bo_users', 'script_media', type_='foreignkey')
    op.drop_constraint('fk_script_media_created_by_bo_users', 'script_media', type_='foreignkey')
    op.drop_column('script_media', 'updated_by')
    op.drop_column('script_media', 'created_by')
