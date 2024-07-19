"""add state column to departments

Revision ID: 18f43ac4622f
Revises: 1931b987ce0d
Create Date: 2023-07-26 15:51:05.329701

"""

import sqlalchemy as sa
from alembic import op


revision = "18f43ac4622f"
down_revision = "1931b987ce0d"


def upgrade():
    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("state", sa.String(length=2), server_default="", nullable=False)
        )
        batch_op.drop_index("ix_departments_name")
        batch_op.create_unique_constraint("departments_name_state", ["name", "state"])


def downgrade():
    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.drop_constraint("departments_name_state", type_="unique")
        batch_op.create_index("ix_departments_name", ["name"], unique=False)
        batch_op.drop_column("state")
