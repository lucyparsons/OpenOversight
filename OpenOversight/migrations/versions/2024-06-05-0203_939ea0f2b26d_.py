"""Add has_content_warning column to link model

Revision ID: 939ea0f2b26d
Revises: 52d3f6a21dd9
Create Date: 2024-06-05 02:03:29.168771

"""
import sqlalchemy as sa
from alembic import op


revision = "939ea0f2b26d"
down_revision = "52d3f6a21dd9"


def upgrade():
    # This is not expected to impact performance: https://dba.stackexchange.com/a/216153
    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "has_content_warning",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            )
        )


def downgrade():
    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.drop_column("has_content_warning")
