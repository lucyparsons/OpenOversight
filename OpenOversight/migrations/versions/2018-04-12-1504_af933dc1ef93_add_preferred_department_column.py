"""add preferred department column

Revision ID: af933dc1ef93
Revises: 42233d18ac7b
Create Date: 2018-04-12 15:41:33.490603

"""
import sqlalchemy as sa
from alembic import op


revision = "af933dc1ef93"
down_revision = "42233d18ac7b"


def upgrade():
    op.add_column("users", sa.Column("dept_pref", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "users_dept_pref_fkey", "users", "departments", ["dept_pref"], ["id"]
    )


def downgrade():
    op.drop_constraint("users_dept_pref_fkey", "users", type_="foreignkey")
    op.drop_column("users", "dept_pref")
