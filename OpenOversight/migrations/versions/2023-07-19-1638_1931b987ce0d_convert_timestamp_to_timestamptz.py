"""convert timestamp to timestamptz

Revision ID: 1931b987ce0d
Revises: 07ace5f956ca
Create Date: 2023-07-19 16:38:49.233825

"""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func as sql_func


revision = "1931b987ce0d"
down_revision = "07ace5f956ca"


TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")


def upgrade():
    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            server_default=sql_func.now(),
            nullable=False,
            postgresql_using=f"created_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using=f"updated_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            server_default=sql_func.now(),
            nullable=False,
            postgresql_using=f"created_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using=f"updated_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            server_default=sql_func.now(),
            postgresql_using=f"created_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "taken_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using=f"taken_at::timestamptz AT TIME ZONE '{TIMEZONE}'",
        )


def downgrade():
    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.alter_column(
            "taken_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=True,
            postgresql_using=f"taken_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            postgresql_using=f"created_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=True,
            postgresql_using=f"updated_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            nullable=True,
            postgresql_using=f"created_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=True,
            postgresql_using=f"updated_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            nullable=True,
            postgresql_using=f"created_at::timestamp AT TIME ZONE '{TIMEZONE}'",
        )
