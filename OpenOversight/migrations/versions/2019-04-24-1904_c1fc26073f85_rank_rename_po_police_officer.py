"""Rank rename PO -> POLICE OFFICER

Revision ID: c1fc26073f85
Revises: 770ed51b4e16
Create Date: 2019-04-24 19:55:46.168086

"""
from alembic import op


revision = "c1fc26073f85"
down_revision = "770ed51b4e16"


def upgrade():
    op.execute("UPDATE assignments SET rank = 'POLICE OFFICER' WHERE rank = 'PO'")


def downgrade():
    pass
