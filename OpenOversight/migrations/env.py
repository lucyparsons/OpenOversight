import logging
import os
from logging.config import fileConfig

from alembic import context
from flask import current_app
from sqlalchemy import engine_from_config, pool

from OpenOversight.app import create_app, db
from OpenOversight.app.utils.constants import KEY_DATABASE_URI, KEY_ENV, KEY_ENV_DEV


app = create_app(os.environ.get(KEY_ENV, KEY_ENV_DEV))
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
        **current_app.extensions["migrate"].configure_args,
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


with app.app_context():
    config.set_main_option("sqlalchemy.url", current_app.config.get(KEY_DATABASE_URI))
    target_metadata = current_app.extensions["migrate"].db.metadata

    db.app = app
    db.create_all()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
