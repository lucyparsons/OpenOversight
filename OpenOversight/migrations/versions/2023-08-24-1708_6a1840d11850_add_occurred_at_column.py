"""add occurred_at column

Revision ID: 6a1840d11850
Revises: 52d3f6a21dd9
Create Date: 2023-08-24 17:08:56.004851

"""
import os

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "6a1840d11850"
down_revision = "52d3f6a21dd9"
branch_labels = None
depends_on = None


TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_incidents_occurred_at"), ["occurred_at"], unique=False
        )

    op.execute(
        f"""
            UPDATE incidents
            SET
                occurred_at = (date::date || ' ' || time::timetz)::timestamp AT TIME ZONE '{TIMEZONE}',
                time = NULL,
                date = NULL
            WHERE occurred_at IS NULL
            AND time IS NOT NULL
            AND date IS NOT NULL
        """
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        f"""
            UPDATE incidents
            SET (date, time) = (occurred_at::date, (occurred_at::timestamptz AT TIME ZONE '{TIMEZONE}')::time)
            WHERE occurred_at IS NOT NULL
        """
    )

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_incidents_occurred_at"))
        batch_op.drop_column("occurred_at")

    # ### end Alembic commands ###
