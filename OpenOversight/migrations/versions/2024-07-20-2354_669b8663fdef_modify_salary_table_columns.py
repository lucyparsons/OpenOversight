"""modify salary table columns

Revision ID: 669b8663fdef
Revises: 939ea0f2b26d
Create Date: 2024-07-20 23:54:04.176103

"""
from alembic import op
import sqlalchemy as sa
from OpenOversight.app.models.database import Currency



revision = '669b8663fdef'
down_revision = '939ea0f2b26d'


def upgrade():
    with op.batch_alter_table('salaries', schema=None) as batch_op:
        batch_op.alter_column('salary',
               existing_type=sa.NUMERIC(),
               type_=Currency(),
               existing_nullable=False)
        batch_op.alter_column('overtime_pay',
               existing_type=sa.NUMERIC(),
               type_=Currency(),
               existing_nullable=True)


def downgrade():
    op.execute(
        """
            ALTER TABLE salaries 
            ALTER COLUMN overtime_pay TYPE NUMERIC 
            USING overtime_pay::NUMERIC
        """
    )

    op.execute(
        """
            ALTER TABLE salaries 
            ALTER COLUMN salary TYPE NUMERIC 
            USING salary::NUMERIC
        """
    )
