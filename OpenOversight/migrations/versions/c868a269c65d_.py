"""empty message

Revision ID: c868a269c65d
Revises: e2c2efde8b55
Create Date: 2019-02-05 07:13:34.930952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c868a269c65d'
down_revision = 'e2c2efde8b55'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assignments', sa.Column('supervisor_star_no', sa.String(length=120), nullable=True))
    op.create_index(op.f('ix_assignments_supervisor_star_no'), 'assignments', ['supervisor_star_no'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_assignments_supervisor_star_no'), table_name='assignments')
    op.drop_column('assignments', 'supervisor_star_no')
    # ### end Alembic commands ###
