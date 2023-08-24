"""change type of star_no to string

Revision ID: 42233d18ac7b
Revises: 114919b27a9f
Create Date: 2017-12-23 18:03:07.304611

"""
import sqlalchemy as sa
from alembic import op


revision = "42233d18ac7b"
down_revision = "114919b27a9f"


def upgrade():
    op.alter_column(
        "assignments",
        "star_no",
        existing_type=sa.INTEGER(),
        type_=sa.String(length=120),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "assignments",
        "star_no",
        existing_type=sa.String(length=120),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )
