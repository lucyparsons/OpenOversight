"""add remaining audit fields to users table

Revision ID: 0a7c591e13b9
Revises: 5865f488470c
Create Date: 2024-10-09 18:59:15.546419

"""
from alembic import op
import sqlalchemy as sa



revision = '0a7c591e13b9'
down_revision = '5865f488470c'


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('confirmed_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('approved_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('disabled_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'users', ['disabled_by'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'users', ['confirmed_by'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key(None, 'users', ['approved_by'], ['id'], ondelete='SET NULL')

    op.execute(
        """
            UPDATE users
            SET approved_at =  NOW()
            WHERE approved IS TRUE
        """
    )

    op.execute(
        """
            UPDATE users
            SET approved_by =  (
                SELECT id
                FROM users
                WHERE is_administrator is TRUE
                ORDER BY created_at ASC
                LIMIT 1
            )
            WHERE approved IS TRUE
        """
    )

    op.execute(
        """
            UPDATE users
            SET confirmed_at =  NOW()
            WHERE confirmed IS TRUE
        """
    )

    op.execute(
        """
            UPDATE users
            SET confirmed_by =  (
                SELECT id
                FROM users
                WHERE is_administrator is TRUE
                ORDER BY created_at ASC
                LIMIT 1
            )
            WHERE confirmed IS TRUE
        """
    )

    op.execute(
        """
            UPDATE users
            SET disabled_at =  NOW()
            WHERE is_disabled IS TRUE
        """
    )

    op.execute(
        """
            UPDATE users
            SET disabled_by =  (
                SELECT id
                FROM users
                WHERE is_administrator is TRUE
                ORDER BY created_at ASC
                LIMIT 1
            )
            WHERE is_disabled IS TRUE
        """
    )



def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('disabled_by')
        batch_op.drop_column('disabled_at')
        batch_op.drop_column('approved_by')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('confirmed_by')
        batch_op.drop_column('confirmed_at')
