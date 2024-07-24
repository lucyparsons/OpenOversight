"""change salary column types

Revision ID: 5865f488470c
Revises: 939ea0f2b26d
Create Date: 2024-07-22 05:38:36.531798

"""

import sqlalchemy as sa
from alembic import op


revision = "5865f488470c"
down_revision = "939ea0f2b26d"


def upgrade():
    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.alter_column(
            "salary",
            existing_type=sa.NUMERIC(),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "overtime_pay",
            existing_type=sa.NUMERIC(),
            type_=sa.Float(),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.alter_column(
            "overtime_pay",
            existing_type=sa.Float(),
            type_=sa.NUMERIC(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "salary",
            existing_type=sa.Float(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
        )
