"""add _uuid column to users

Revision ID: 52d3f6a21dd9
Revises: a35aa1a114fa
Create Date: 2023-07-24 16:19:01.375427

"""
import uuid

import sqlalchemy as sa
from alembic import op


revision = "52d3f6a21dd9"
down_revision = "a35aa1a114fa"


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "_uuid",
            sa.String(36),
            nullable=False,
            server_default=lambda: str(uuid.uuid4()),
        ),
    )
    op.create_index(op.f("ix_users__uuid"), "users", ["_uuid"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_users__uuid"), table_name="users")
    op.drop_column("users", "_uuid")
