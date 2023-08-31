"""Add unique_internal_identifier to officers table

Revision ID: 2c27bfebe66e
Revises: 7bb53dee8ac9
Create Date: 2018-08-18 13:36:00.987327

"""
import sqlalchemy as sa
from alembic import op


revision = "2c27bfebe66e"
down_revision = "7bb53dee8ac9"


def upgrade():
    op.add_column(
        "officers",
        sa.Column("unique_internal_identifier", sa.String(length=50), nullable=True),
    )
    op.create_index(
        op.f("ix_officers_unique_internal_identifier"),
        "officers",
        ["unique_internal_identifier"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix_officers_unique_internal_identifier"), table_name="officers")
    op.drop_column("officers", "unique_internal_identifier")
