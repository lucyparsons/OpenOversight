"""Add order to jobs in DB and adjust constraints on order column

Revision ID: 562bd5f1bc1f
Revises: 6045f42587ec
Create Date: 2020-04-24 01:58:05.146902

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = '562bd5f1bc1f'
down_revision = '6045f42587ec'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    job = table('jobs', 
        column('department_id', sa.Integer),
        column('order', sa.Integer)
        )
    
    department = table('departments',
        column('id', sa.Integer),
        column('name', sa.String)
    )

    op.drop_constraint('unique_department_job_order', 'jobs', type_='unique')

    all_depts = connection.execute(department.select()).fetchall()
    for dept in all_depts:
        job_order = 0
        connection.execute(
            job.update().values({"order" : job_order}).where(sa.and_(job.c.department_id == dept.id, job.c.order.is_(None)))
        )

    op.alter_column('jobs', 'order',
                    existing_type=sa.INTEGER(),
                    nullable=False)


def downgrade():
    op.create_unique_constraint('unique_department_job_order', 'jobs', ['order', 'department_id'])

    op.alter_column('jobs', 'order',
                    existing_type=sa.INTEGER(),
                    nullable=True)
