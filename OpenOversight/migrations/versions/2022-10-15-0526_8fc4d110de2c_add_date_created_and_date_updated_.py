"""Add date_created and date_updated to assignments, incidents, officers tables.

Revision ID: 8fc4d110de2c
Revises: cd39b33b5360
Create Date: 2022-10-12 05:26:07.671962

"""
import sqlalchemy as sa
from alembic import op


revision = "8fc4d110de2c"
down_revision = "cd39b33b5360"


def upgrade():
    op.add_column(
        "assignments", sa.Column("date_created", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "assignments", sa.Column("date_updated", sa.DateTime(), nullable=True)
    )
    op.create_index(
        op.f("ix_assignments_date_updated"),
        "assignments",
        ["date_updated"],
        unique=False,
    )

    op.add_column("incidents", sa.Column("date_created", sa.DateTime(), nullable=True))
    op.add_column("incidents", sa.Column("date_updated", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_incidents_date_updated"), "incidents", ["date_updated"], unique=False
    )

    op.add_column("officers", sa.Column("date_created", sa.DateTime(), nullable=True))
    op.add_column("officers", sa.Column("date_updated", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_officers_date_updated"), "officers", ["date_updated"], unique=False
    )

    op.execute(
        """
        update officers
        set date_created='2021-12-28',
            date_updated='2021-12-28';
        """
    )


def downgrade():
    op.drop_index(op.f("ix_officers_date_updated"), table_name="officers")
    op.drop_column("officers", "date_updated")
    op.drop_column("officers", "date_created")

    op.drop_index(op.f("ix_incidents_date_updated"), table_name="incidents")
    op.drop_column("incidents", "date_updated")
    op.drop_column("incidents", "date_created")

    op.drop_index(op.f("ix_assignments_date_updated"), table_name="assignments")
    op.drop_column("assignments", "date_updated")
    op.drop_column("assignments", "date_created")
