"""Add approved boolean to users table

Revision ID: 5c5b80cab45e
Revises: 9e2827dae28c
Create Date: 2019-01-24 15:54:08.123125

"""
import sqlalchemy as sa
from alembic import op


revision = "5c5b80cab45e"
down_revision = "e2c2efde8b55"


def upgrade():
    op.add_column("users", sa.Column("approved", sa.Boolean(), default=False))
    op.execute("UPDATE users SET approved=True")


def downgrade():
    op.drop_column("users", "approved")
