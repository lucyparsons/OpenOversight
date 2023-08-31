"""add area coordinator columns

Revision ID: e14a1aa4b58f
Revises: af933dc1ef93
Create Date: 2018-04-30 15:48:51.968189

"""
import sqlalchemy as sa
from alembic import op


revision = "e14a1aa4b58f"
down_revision = "af933dc1ef93"


def upgrade():
    op.add_column("users", sa.Column("ac_department_id", sa.Integer(), nullable=True))
    op.add_column(
        "users", sa.Column("is_area_coordinator", sa.Boolean(), nullable=True)
    )
    op.create_foreign_key(
        "users_ac_department_id_fkey",
        "users",
        "departments",
        ["ac_department_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("users_ac_department_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "is_area_coordinator")
    op.drop_column("users", "ac_department_id")
