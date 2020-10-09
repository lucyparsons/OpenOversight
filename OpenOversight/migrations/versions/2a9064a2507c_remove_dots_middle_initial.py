"""remove_dots_middle_initial

Revision ID: 2a9064a2507c
Revises: 5c5b80cab45e
Create Date: 2019-02-03 05:33:05.296642

"""
from flask import current_app
import os
import sys
# Add our Flask app to the search paths for modules
sys.path.insert(0, os.path.dirname(current_app.root_path))
from app.models import Officer, db  # noqa: E402


# revision identifiers, used by Alembic.
revision = '2a9064a2507c'
down_revision = '5c5b80cab45e'
branch_labels = None
depends_on = None


def upgrade():
    for officer in Officer.query.filter(Officer.middle_initial.in_([".", "-"])).all():
        officer.middle_initial = ""
        db.session.commit()


def downgrade():
    pass
