"""rename user_id to creator_id in incidents

Revision ID: bd0398fe4aab
Revises: f4a41e328a06
Create Date: 2018-05-15 19:56:14.199692

"""
import sqlalchemy as sa
from alembic import op


revision = "bd0398fe4aab"
down_revision = "f4a41e328a06"


def upgrade():
    op.alter_column(
        "incidents", "user_id", new_column_name="creator_id", existing_type=sa.Integer
    )
    op.add_column(
        "incidents", sa.Column("last_updated_id", sa.Integer(), nullable=True)
    )
    op.drop_constraint("incidents_user_id_fkey", "incidents", type_="foreignkey")
    op.create_foreign_key(
        "incidents_creator_id_fkey", "incidents", "users", ["creator_id"], ["id"]
    )
    op.create_foreign_key(
        "incidents_last_updated_id_fkey",
        "incidents",
        "users",
        ["last_updated_id"],
        ["id"],
    )


def downgrade():
    op.alter_column(
        "incidents", "creator_id", new_column_name="user_id", existing_type=sa.Integer
    )
    op.drop_constraint("incidents_creator_id_fkey", "incidents", type_="foreignkey")
    op.drop_constraint(
        "incidents_last_updated_id_fkey", "incidents", type_="foreignkey"
    )
    op.create_foreign_key(
        "incidents_user_id_fkey", "incidents", "users", ["user_id"], ["id"]
    )
    op.drop_column("incidents", "last_updated_id")
