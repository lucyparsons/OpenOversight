"""Add email last sent columns

Revision ID: edab445d1714
Revises: 99c50fc8d294
Create Date: 2025-04-04 08:42:14.823515

"""

import sqlalchemy as sa
from alembic import op


revision = "edab445d1714"
down_revision = "99c50fc8d294"


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_confirmation_sent_at", sa.DateTime(timezone=True), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("last_reset_sent_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("last_reset_sent_at")
        batch_op.drop_column("last_confirmation_sent_at")
