"""initial migration

Revision ID: 114919b27a9f
Revises:
Create Date: 2017-12-10 05:20:45.748342

"""
import sqlalchemy as sa
from alembic import op


revision = "114919b27a9f"
down_revision = None


def upgrade():
    op.drop_table("migrate_version")
    op.add_column("officers", sa.Column("department_id", sa.Integer(), nullable=True))
    op.drop_index("ix_officers_pd_id", table_name="officers")
    op.create_foreign_key(
        "officers_department_id_fkey",
        "officers",
        "departments",
        ["department_id"],
        ["id"],
    )
    op.drop_column("officers", "pd_id")
    op.add_column("unit_types", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "unit_types_department_id_fkey",
        "unit_types",
        "departments",
        ["department_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "unit_types_department_id_fkey", "unit_types", type_="foreignkey"
    )
    op.drop_column("unit_types", "department_id")
    op.add_column(
        "officers", sa.Column("pd_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.drop_constraint("officers_department_id_fkey", "officers", type_="foreignkey")
    op.create_index("ix_officers_pd_id", "officers", ["pd_id"], unique=False)
    op.drop_column("officers", "department_id")
    op.create_table(
        "migrate_version",
        sa.Column(
            "repository_id", sa.VARCHAR(length=250), autoincrement=False, nullable=False
        ),
        sa.Column("repository_path", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("version", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("repository_id", name="migrate_version_pkey"),
    )
