"""add explicit ondelete for notes

Revision ID: 8ce7926aa132
Revises: cfc5f3fd5efe
Create Date: 2018-06-07 18:53:47.656557

"""
from alembic import op


revision = "8ce7926aa132"
down_revision = "cfc5f3fd5efe"


def upgrade():
    op.drop_constraint("notes_officer_id_fkey", "notes", type_="foreignkey")
    op.drop_constraint("notes_creator_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_officer_id_fkey",
        "notes",
        "officers",
        ["officer_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "notes_creator_id_fkey",
        "notes",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("notes_officer_id_fkey", "notes", type_="foreignkey")
    op.drop_constraint("notes_creator_id_fkey", "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_creator_id_fkey", "notes", "users", ["creator_id"], ["id"]
    )
    op.create_foreign_key(
        "notes_officer_id_fkey", "notes", "officers", ["officer_id"], ["id"]
    )
