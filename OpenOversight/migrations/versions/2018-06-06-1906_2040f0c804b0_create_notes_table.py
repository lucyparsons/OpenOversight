"""create notes table

Revision ID: 2040f0c804b0
Revises: bd0398fe4aab
Create Date: 2018-06-06 19:34:16.439093

"""
import sqlalchemy as sa
from alembic import op


revision = "2040f0c804b0"
down_revision = "bd0398fe4aab"


def upgrade():
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("officer_id", sa.Integer(), nullable=True),
        sa.Column("date_created", sa.DateTime(), nullable=True),
        sa.Column("date_updated", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["officer_id"], ["officers.id"], "notes_officer_id_fkey"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], "notes_user_id_fkey"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("notes")
