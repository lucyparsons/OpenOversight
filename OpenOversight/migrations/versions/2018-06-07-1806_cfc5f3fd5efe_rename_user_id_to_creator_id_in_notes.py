"""rename user_id to creator_id in notes

Revision ID: cfc5f3fd5efe
Revises: 2040f0c804b0
Create Date: 2018-06-07 18:52:31.059396

"""
import sqlalchemy as sa
from alembic import op


revision = "cfc5f3fd5efe"
down_revision = "2040f0c804b0"


def upgrade():
    op.add_column("notes", sa.Column("creator_id", sa.Integer(), nullable=True))
    op.drop_constraint("notes_user_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_creator_id_fkey", "notes", "users", ["creator_id"], ["id"]
    )
    op.drop_column("notes", "user_id")


def downgrade():
    op.add_column(
        "notes", sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.drop_constraint("notes_creator_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key("notes_user_id_fkey", "notes", "users", ["user_id"], ["id"])
    op.drop_column("notes", "creator_id")
