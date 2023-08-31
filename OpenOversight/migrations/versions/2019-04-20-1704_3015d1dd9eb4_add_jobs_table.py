"""Add Jobs table

Revision ID: 3015d1dd9eb4
Revises: c1fc26073f85
Create Date: 2019-04-20 17:54:41.661851

"""
import sqlalchemy as sa
from alembic import op


revision = "3015d1dd9eb4"
down_revision = "c1fc26073f85"


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("is_sworn_officer", sa.Boolean(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.id"], "jobs_department_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_title", "department_id", name="unique_department_job_titles"
        ),
        sa.UniqueConstraint(
            "order", "department_id", name="unique_department_job_order"
        ),
    )
    op.create_index(
        op.f("ix_jobs_is_sworn_officer"), "jobs", ["is_sworn_officer"], unique=False
    )
    op.create_index(op.f("ix_jobs_job_title"), "jobs", ["job_title"], unique=False)
    op.create_index(op.f("ix_jobs_order"), "jobs", ["order"], unique=False)
    op.execute(
        """
INSERT INTO
  jobs (job_title, is_sworn_officer, department_id)
SELECT DISTINCT
  assignments.rank,
  True,
  officers.department_id
FROM
  assignments
  INNER JOIN officers ON assignments.officer_id = officers.id"""
    )
    op.add_column("assignments", sa.Column("job_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_job_assignment", "assignments", "jobs", ["job_id"], ["id"]
    )
    op.execute(
        """
UPDATE
  assignments
SET
  job_id = jobs.id
FROM
  officers
  INNER JOIN jobs ON jobs.department_id = officers.department_id
WHERE
  assignments.rank = jobs.job_title
  AND assignments.officer_id = officers.id"""
    )
    op.drop_index("ix_assignments_rank", table_name="assignments")
    op.drop_column("assignments", "rank")
    op.alter_column("assignments", "unit", new_column_name="unit_id")


def downgrade():
    op.alter_column("assignments", "unit_id", new_column_name="unit")
    op.add_column(
        "assignments",
        sa.Column("rank", sa.VARCHAR(length=120), autoincrement=False, nullable=True),
    )
    op.create_index("ix_assignments_rank", "assignments", ["rank"], unique=False)
    op.execute(
        """
UPDATE
  assignments
SET
  rank = jobs.job_title
FROM
  jobs
WHERE
  assignments.job_id = jobs.id"""
    )
    op.drop_constraint("fk_job_assignment", "assignments", type_="foreignkey")
    op.drop_column("assignments", "job_id")
    op.drop_index(op.f("ix_jobs_order"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_title"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_is_sworn_officer"), table_name="jobs")
    op.drop_table("jobs")
