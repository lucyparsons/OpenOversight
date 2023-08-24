"""Add featured flag to faces table

Revision ID: 79a14685454f
Revises: 562bd5f1bc1f
Create Date: 2020-07-31 14:03:59.871182

"""
import sqlalchemy as sa
from alembic import op


revision = "79a14685454f"
down_revision = "562bd5f1bc1f"


def upgrade():
    op.add_column(
        "faces",
        sa.Column("featured", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade():
    op.drop_column("faces", "featured")
