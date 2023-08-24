"""Add cascading foreign key constraint to assignments

Revision ID: 9e2827dae28c
Revises: 0acbb0f0b1ef
Create Date: 2018-08-13 13:18:15.381300

"""
from alembic import op


revision = "9e2827dae28c"
down_revision = "0acbb0f0b1ef"


def upgrade():
    op.drop_constraint("assignments_officer_id_fkey", "assignments", type_="foreignkey")
    op.create_foreign_key(
        "assignments_officer_id_fkey",
        "assignments",
        "officers",
        ["officer_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("assignments_officer_id_fkey", "assignments", type_="foreignkey")
    op.create_foreign_key(
        "assignments_officer_id_fkey", "assignments", "officers", ["officer_id"], ["id"]
    )
