"""Remove character limit of url field in link model.

Revision ID: 93fc3e074dcc
Revises: cd39b33b5360
Create Date: 2022-01-05 06:50:40.070530

"""
import sqlalchemy as sa
from alembic import op


revision = "93fc3e074dcc"
down_revision = "cd39b33b5360"


def upgrade():
    op.alter_column(
        "links",
        "url",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "links",
        "url",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=False,
    )
