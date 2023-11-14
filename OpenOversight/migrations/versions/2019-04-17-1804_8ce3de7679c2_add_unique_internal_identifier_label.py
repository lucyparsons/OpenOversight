"""adds unique_internal_identifier_label to departments table

Revision ID: 8ce3de7679c2
Revises: 3015d1dd9eb4
Create Date: 2019-04-17 18:26:35.733783

"""
import sqlalchemy as sa
from alembic import op


revision = "8ce3de7679c2"
down_revision = "3015d1dd9eb4"


def upgrade():
    op.add_column(
        "departments",
        sa.Column(
            "unique_internal_identifier_label", sa.String(length=100), nullable=True
        ),
    )


def downgrade():
    op.drop_column("departments", "unique_internal_identifier_label")
