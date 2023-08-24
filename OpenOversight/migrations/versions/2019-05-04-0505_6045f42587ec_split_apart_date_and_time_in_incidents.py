"""Split apart date and time in incidents

Revision ID: 6045f42587ec
Revises: 8ce3de7679c2
Create Date: 2019-05-04 05:28:06.869101

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "6045f42587ec"
down_revision = "8ce3de7679c2"


def upgrade():
    op.add_column("incidents", sa.Column("time", sa.Time(), nullable=True))
    op.execute("UPDATE incidents SET time = date::time")
    op.alter_column(
        "incidents",
        "date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.Date(),
        existing_nullable=True,
    )
    op.create_index(op.f("ix_incidents_time"), "incidents", ["time"], unique=False)
    op.execute(
        'UPDATE incidents SET "time" = NULL WHERE "time" = \'01:02:03.045678\'::time'
    )


def downgrade():
    op.execute(
        "UPDATE incidents SET \"time\" = '01:02:03.045678'::time WHERE time IS NULL"
    )
    op.drop_index(op.f("ix_incidents_time"), table_name="incidents")
    op.alter_column(
        "incidents",
        "date",
        existing_type=sa.Date(),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.execute("UPDATE incidents SET date = date + time")
    op.drop_column("incidents", "time")
