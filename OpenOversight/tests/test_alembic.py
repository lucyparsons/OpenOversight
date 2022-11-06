from alembic.script import ScriptDirectory
from flask import current_app


def test_alembic_has_single_head(session):
    """
    Avoid unintentional branches in the migration history.
    """
    migrations_dir = current_app.extensions["migrate"].directory
    heads = ScriptDirectory(migrations_dir).get_heads()

    assert len(heads) == 1
