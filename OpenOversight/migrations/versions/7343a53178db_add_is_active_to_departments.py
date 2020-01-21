"""adds the is_active boolean column to departments

Revision ID: 7343a53178db
Revises: 8ce3de7679c2
Create Date: 2019-03-15 14:35:20.801060

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7343a53178db'
down_revision = '6045f42587ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('departments', sa.Column('is_active', sa.Boolean(), nullable=False, server_default="True"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('departments', 'is_active')
    # ### end Alembic commands ###