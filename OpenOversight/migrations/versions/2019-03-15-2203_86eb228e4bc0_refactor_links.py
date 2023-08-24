"""Refactor links

Revision ID: 86eb228e4bc0
Revises: 79a14685454f
Create Date: 2019-03-15 22:40:10.473917

"""
from alembic import op


revision = "86eb228e4bc0"
down_revision = "79a14685454f"


def upgrade():
    op.drop_constraint("links_user_id_fkey", "links", type_="foreignkey")
    op.alter_column("links", "user_id", new_column_name="creator_id")
    op.create_foreign_key(
        "links_creator_id_fkey",
        "links",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("links_creator_id_fkey", "links", type_="foreignkey")
    op.alter_column("links", "creator_id", new_column_name="user_id")
    op.create_foreign_key("links_user_id_fkey", "links", "users", ["user_id"], ["id"])
