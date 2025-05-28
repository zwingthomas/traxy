"""Initial tables
Revision ID: 20250528_initial
Revises:
Create Date: 2025-05-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String, unique=True, index=True),
        sa.Column('hashed_password', sa.String),
    )
    op.create_table('trackers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('name', sa.String),
        sa.Column('color', sa.String),
        sa.Column('rule', sa.JSON),
        sa.Column('visibility', sa.String),
    )
    op.create_table('activities',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tracker_id', sa.Integer, sa.ForeignKey('trackers.id')),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('value', sa.Integer),
    )
    op.create_table('friendships',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('friend_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    )

def downgrade():
    op.drop_table('friendships')
    op.drop_table('activities')
    op.drop_table('trackers')
    op.drop_table('users')