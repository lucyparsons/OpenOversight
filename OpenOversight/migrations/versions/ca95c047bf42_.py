"""add department column to incidents

Revision ID: ca95c047bf42
Revises: 6065d7cdcbf8
Create Date: 2018-05-10 20:02:19.006081

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "ca95c047bf42"
down_revision = "6065d7cdcbf8"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("incidents", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "incidents", "departments", ["department_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "incidents", type_="foreignkey")
    op.drop_column("incidents", "department_id")
    # ### end Alembic commands ###
