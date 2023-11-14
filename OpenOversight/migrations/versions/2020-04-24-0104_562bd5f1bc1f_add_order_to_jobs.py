"""Add order to jobs in DB and adjust constraints on order column

Revision ID: 562bd5f1bc1f
Revises: 6045f42587ec
Create Date: 2020-04-24 01:58:05.146902

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table


revision = "562bd5f1bc1f"
down_revision = "6045f42587ec"


def upgrade():
    connection = op.get_bind()
    job = table(
        "jobs", column("department_id", sa.Integer), column("order", sa.Integer)
    )

    department = table(
        "departments", column("id", sa.Integer), column("name", sa.String)
    )

    op.drop_constraint("unique_department_job_order", "jobs", type_="unique")
    op.drop_index(op.f("ix_jobs_order"), table_name="jobs")

    all_depts = connection.execute(department.select()).fetchall()
    for dept in all_depts:
        job_order = 0
        connection.execute(
            job.update()
            .values({"order": job_order})
            .where(sa.and_(job.c.department_id == dept.id, job.c.order.is_(None)))
        )

    op.alter_column("jobs", "order", existing_type=sa.INTEGER(), nullable=False)


def downgrade():
    op.alter_column("jobs", "order", existing_type=sa.INTEGER(), nullable=True)
