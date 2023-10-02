import logging
import os
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, render_template, request
from flask_bootstrap import Bootstrap
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sitemap import Sitemap
from flask_wtf.csrf import CSRFProtect

from OpenOversight.app.email_client import EmailClient
from OpenOversight.app.filters import instantiate_filters
from OpenOversight.app.models.config import config
from OpenOversight.app.models.database import db
from OpenOversight.app.models.users import AnonymousUser
from OpenOversight.app.utils.constants import MEGABYTE


bootstrap = Bootstrap()
compress = Compress()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.anonymous_user = AnonymousUser
login_manager.login_view = "auth.login"

limiter = Limiter(
    key_func=get_remote_address, default_limits=["100 per minute", "5 per second"]
)

sitemap = Sitemap()
csrf = CSRFProtect()


def create_app(config_name="default"):
    app = Flask(__name__)
    # Creates and adds the Config object of the correct type to app.config
    app.config.from_object(config[config_name])

    bootstrap.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        EmailClient()
    limiter.init_app(app)
    login_manager.init_app(app)
    sitemap.init_app(app)
    compress.init_app(app)

    from OpenOversight.app.main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from OpenOversight.app.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    max_log_size = 10 * MEGABYTE  # start new log file after 10 MB
    num_logs_to_keep = 5
    file_handler = RotatingFileHandler(
        "/tmp/openoversight.log", "a", max_log_size, num_logs_to_keep
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )

    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("OpenOversight startup")

    # Also log when endpoints are getting hit hard
    limiter.logger.addHandler(file_handler)

    # Define error handlers
    def create_errorhandler(code, error, template):
        """
        Create an error handler that returns a JSON or a template response
        based on the request "Accept" header.
        :param code: status code to handle
        :param error: response error message, if JSON
        :param template: template response
        """

        def _handler_method(e):
            if request.accept_mimetypes.best == "application/json":
                return jsonify(error=error), code
            return render_template(template), code

        return _handler_method

    error_handlers = [
        (HTTPStatus.FORBIDDEN, HTTPStatus.FORBIDDEN.phrase, "403.html"),
        (HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase, "404.html"),
        (
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE.phrase,
            "413.html",
        ),
        (HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.TOO_MANY_REQUESTS.phrase, "429.html"),
        (
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            "500.html",
        ),
    ]
    for code, error, template in error_handlers:
        # Pass generated errorhandler function to @app.errorhandler decorator
        app.errorhandler(code)(create_errorhandler(code, error, template))

    # Instantiate filters
    instantiate_filters(app)

    # Add commands
    Migrate(
        app, db, os.path.join(os.path.dirname(__file__), "..", "migrations")
    )  # Adds 'db' command
    from OpenOversight.app.commands import (
        add_department,
        add_job_title,
        advanced_csv_import,
        bulk_add_officers,
        link_images_to_department,
        link_officers_to_department,
        make_admin_user,
    )

    app.cli.add_command(make_admin_user)
    app.cli.add_command(link_images_to_department)
    app.cli.add_command(link_officers_to_department)
    app.cli.add_command(bulk_add_officers)
    app.cli.add_command(add_department)
    app.cli.add_command(add_job_title)
    app.cli.add_command(advanced_csv_import)

    # locale.setlocale(locale.LC_ALL, '')

    return app


app = create_app()
