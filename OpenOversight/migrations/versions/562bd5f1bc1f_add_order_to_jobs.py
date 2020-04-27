"""Add order to jobs in DB and adjust constraints on order column

Revision ID: 562bd5f1bc1f
Revises: 6045f42587ec
Create Date: 2020-04-24 01:58:05.146902

"""
from alembic import op
import sqlalchemy as sa
from app.models import Department, Job, db


# revision identifiers, used by Alembic.
revision = '562bd5f1bc1f'
down_revision = '6045f42587ec'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('unique_department_job_order', 'jobs', type_='unique')

    for department in Department.query.all():
        job_order = 0
        for job in Job.query.filter_by(department_id=department.id):
            job.order = job_order
            job_order += 1
    db.session.commit()

    op.alter_column('jobs', 'order',
                    existing_type=sa.INTEGER(),
                    nullable=False)


def downgrade():
    op.create_unique_constraint('unique_department_job_order', 'jobs', ['order', 'department_id'])

    op.alter_column('jobs', 'order',
                    existing_type=sa.INTEGER(),
                    nullable=True)
