"""rename 'descrip' to 'description'

Revision ID: eb0266dc8588
Revises: 9ce70d7ebd56
Create Date: 2023-07-18 19:21:43.632936

"""
from alembic import op


revision = "eb0266dc8588"
down_revision = "9ce70d7ebd56"


def upgrade():
    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.drop_index("ix_unit_types_descrip")
        batch_op.alter_column("descrip", nullable=True, new_column_name="description")
        batch_op.create_index(
            "ix_unit_types_description", ["description"], unique=False
        )


def downgrade():
    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.drop_index("ix_unit_types_description")
        batch_op.alter_column("description", nullable=True, new_column_name="descrip")
        batch_op.create_index("ix_unit_types_descrip", ["descrip"], unique=False)
