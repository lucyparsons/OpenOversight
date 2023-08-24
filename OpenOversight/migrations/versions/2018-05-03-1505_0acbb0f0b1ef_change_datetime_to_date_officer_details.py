"""change datetime to date officer details

Revision ID: 0acbb0f0b1ef
Revises: af933dc1ef93
Create Date: 2018-05-03 15:00:36.849627

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0acbb0f0b1ef"
down_revision = "0ed957db0058"


def upgrade():
    op.alter_column(
        "assignments",
        "resign_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.Date(),
        existing_nullable=True,
    )
    op.alter_column(
        "assignments",
        "star_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.Date(),
        existing_nullable=True,
    )
    op.alter_column(
        "officers",
        "employment_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.Date(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "officers",
        "employment_date",
        existing_type=sa.Date(),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.alter_column(
        "assignments",
        "star_date",
        existing_type=sa.Date(),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.alter_column(
        "assignments",
        "resign_date",
        existing_type=sa.Date(),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
