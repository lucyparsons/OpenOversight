"""add department column to incidents

Revision ID: ca95c047bf42
Revises: 6065d7cdcbf8
Create Date: 2018-05-10 20:02:19.006081

"""
import sqlalchemy as sa
from alembic import op


revision = "ca95c047bf42"
down_revision = "6065d7cdcbf8"


def upgrade():
    op.add_column("incidents", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "incidents_department_id_fkey",
        "incidents",
        "departments",
        ["department_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("incidents_department_id_fkey", "incidents", type_="foreignkey")
    op.drop_column("incidents", "department_id")
