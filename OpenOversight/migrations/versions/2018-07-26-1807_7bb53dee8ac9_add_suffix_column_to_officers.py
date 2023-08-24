"""Add suffix column to officers

Revision ID: 7bb53dee8ac9
Revises: 59e9993c169c
Create Date: 2018-07-26 18:36:10.061968

"""
import sqlalchemy as sa
from alembic import op


revision = "7bb53dee8ac9"
down_revision = "59e9993c169c"


def upgrade():
    op.add_column("officers", sa.Column("suffix", sa.String(length=120), nullable=True))
    op.create_index(op.f("ix_officers_suffix"), "officers", ["suffix"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_officers_suffix"), table_name="officers")
    op.drop_column("officers", "suffix")
