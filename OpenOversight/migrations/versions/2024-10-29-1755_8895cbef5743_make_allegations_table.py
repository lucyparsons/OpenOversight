"""make allegations table

Revision ID: 8895cbef5743
Revises: 99c50fc8d294
Create Date: 2024-10-29 17:55:02.500162

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "8895cbef5743"
down_revision = "99c50fc8d294"


def upgrade():
    op.create_table(
        "allegations",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "last_updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("incident_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("officer_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("disposition", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("discipline", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("type", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("finding", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("created_by", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("last_updated_by", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="allegations_created_by_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], name="allegations_incident_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["last_updated_by"],
            ["users.id"],
            name="allegations_last_updated_by_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["officer_id"], ["officers.id"], name="allegations_officer_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="allegations_pkey"),
    )


def downgrade():
    op.drop_table("allegations")
