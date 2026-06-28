"""add_script_media_table

Revision ID: 3f8a92b1c045
Revises: 254d4e3df0ee
Create Date: 2026-06-01 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '3f8a92b1c045'
down_revision = '254d4e3df0ee'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'script_media',
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
        sa.Column('script_id', sa.BigInteger(), nullable=False, comment='脚本ID'),
        sa.Column('media_type', sa.Integer(), nullable=False, comment='素材类型'),
        sa.Column('status', sa.Integer(), nullable=False, comment='状态'),
        sa.Column('media_id', sa.BigInteger(), nullable=True, comment='生成的媒体文件ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['bo_users.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['bo_users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_script_media_created_at'), 'script_media', ['created_at'], unique=False)
    op.create_index(op.f('ix_script_media_media_type'), 'script_media', ['media_type'], unique=False)
    op.create_index(op.f('ix_script_media_script_id'), 'script_media', ['script_id'], unique=False)
    op.create_index(op.f('ix_script_media_status'), 'script_media', ['status'], unique=False)
    op.create_index(op.f('ix_script_media_updated_at'), 'script_media', ['updated_at'], unique=False)
    op.create_index(op.f('ix_script_media_user_id'), 'script_media', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_script_media_user_id'), table_name='script_media')
    op.drop_index(op.f('ix_script_media_updated_at'), table_name='script_media')
    op.drop_index(op.f('ix_script_media_status'), table_name='script_media')
    op.drop_index(op.f('ix_script_media_script_id'), table_name='script_media')
    op.drop_index(op.f('ix_script_media_media_type'), table_name='script_media')
    op.drop_index(op.f('ix_script_media_created_at'), table_name='script_media')
    op.drop_table('script_media')
