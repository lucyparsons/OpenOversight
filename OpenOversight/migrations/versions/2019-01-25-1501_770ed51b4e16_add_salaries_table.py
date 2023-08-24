"""Add salaries table

Revision ID: 770ed51b4e16
Revises: 2a9064a2507c
Create Date: 2019-01-25 15:47:13.812837

"""
import sqlalchemy as sa
from alembic import op


revision = "770ed51b4e16"
down_revision = "2a9064a2507c"


def upgrade():
    op.create_table(
        "salaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("officer_id", sa.Integer(), nullable=False),
        sa.Column("salary", sa.Numeric(), nullable=False),
        sa.Column("overtime_pay", sa.Numeric(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("is_fiscal_year", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["officer_id"],
            ["officers.id"],
            "salaries_officer_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_salary_overtime_pay"), "salaries", ["overtime_pay"], unique=False
    )
    op.create_index(op.f("ix_salary_salary"), "salaries", ["salary"], unique=False)
    op.create_index(op.f("ix_salary_year"), "salaries", ["year"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_salary_year"), table_name="salaries")
    op.drop_index(op.f("ix_salary_salary"), table_name="salaries")
    op.drop_index(op.f("ix_salary_overtime_pay"), table_name="salaries")
    op.drop_table("salaries")
