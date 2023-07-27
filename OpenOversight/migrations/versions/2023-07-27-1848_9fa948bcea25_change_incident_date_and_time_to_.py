"""change incident date and time to timestamptz

Revision ID: 9fa948bcea25
Revises: 18f43ac4622f
Create Date: 2023-07-27 18:48:58.819477

"""
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9fa948bcea25'
down_revision = '18f43ac4622f'
branch_labels = None
depends_on = None

TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")


def upgrade():
    op.add_column('incidents', sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True))
    op.execute(
        f"""
            UPDATE incidents
            SET occurred_at = (date::date || ' ' || COALESCE(time, 
                '00:00:00')::timetz)::timestamp AT TIME ZONE '{TIMEZONE}'
            WHERE occurred_at IS NULL
        """
    )
    op.alter_column('incidents', 'occurred_at', nullable=False)
    op.drop_index('ix_incidents_date')
    op.drop_index('ix_incidents_time')
    op.drop_column('incidents', 'time')
    op.drop_column('incidents', 'date')


def downgrade():
    op.add_column('incidents', sa.Column('date', sa.DATE(), nullable=True))
    op.add_column('incidents', sa.Column('time', postgresql.TIME(), nullable=True))
    op.execute(
        f"""
        UPDATE incidents
        SET (date, time) = (occurred_at::date, (occurred_at::timestamptz AT TIME ZONE '{TIMEZONE}')::time)
        """)

    op.create_index(op.f('ix_incidents_time'), 'incidents', ['time'], unique=False)
    op.create_index(op.f('ix_incidents_date'), 'incidents', ['date'], unique=False)
    op.drop_column('incidents', 'occurred_at')
