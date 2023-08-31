"""add columns to incidents and links

Revision ID: f4a41e328a06
Revises: ca95c047bf42
Create Date: 2018-05-15 17:03:06.270691

"""
import sqlalchemy as sa
from alembic import op


revision = "f4a41e328a06"
down_revision = "ca95c047bf42"


def upgrade():
    op.add_column("incidents", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "incidents_user_id_fkey", "incidents", "users", ["user_id"], ["id"]
    )
    op.add_column("links", sa.Column("author", sa.String(length=255), nullable=True))
    op.add_column("links", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("links", sa.Column("title", sa.String(length=100), nullable=True))
    op.add_column("links", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_links_title"), "links", ["title"], unique=False)
    op.create_foreign_key("links_user_id_fkey", "links", "users", ["user_id"], ["id"])


def downgrade():
    op.drop_constraint("links_user_id_fkey", "links", type_="foreignkey")
    op.drop_index(op.f("ix_links_title"), table_name="links")
    op.drop_column("links", "user_id")
    op.drop_column("links", "title")
    op.drop_column("links", "description")
    op.drop_column("links", "author")
    op.drop_constraint("incidents_user_id_fkey", "incidents", type_="foreignkey")
    op.drop_column("incidents", "user_id")
