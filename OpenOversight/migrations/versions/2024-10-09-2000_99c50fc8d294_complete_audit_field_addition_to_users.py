"""complete audit field addition to users

Revision ID: 99c50fc8d294
Revises: bf254c0961ca
Create Date: 2024-10-09 20:00:55.155377

"""

import sqlalchemy as sa
from alembic import op


revision = "99c50fc8d294"
down_revision = "bf254c0961ca"


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("approved")
        batch_op.drop_column("confirmed")
        batch_op.drop_column("is_disabled")


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_disabled", sa.BOOLEAN(), autoincrement=False, nullable=True)
        )
        batch_op.add_column(
            sa.Column("confirmed", sa.BOOLEAN(), autoincrement=False, nullable=True)
        )
        batch_op.add_column(
            sa.Column("approved", sa.BOOLEAN(), autoincrement=False, nullable=True)
        )

    op.execute(
        """
            UPDATE users
            SET is_disabled =  TRUE
            WHERE disabled_at IS NOT NULL
        """
    )

    op.execute(
        """
            UPDATE users
            SET approved =  TRUE
            WHERE approved_at IS NOT NULL
        """
    )

    op.execute(
        """
            UPDATE users
            SET confirmed =  TRUE
            WHERE confirmed_at IS NOT NULL
        """
    )
