import datetime
import logging
import os
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import bleach
import markdown as _markdown
from bleach_allowlist import markdown_attrs, markdown_tags
from flask import Flask, jsonify, render_template, request
from flask_bootstrap import Bootstrap
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sitemap import Sitemap
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup

from .config import config
from .gmail_client import GmailClient


bootstrap = Bootstrap()
GmailClient()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"

limiter = Limiter(
    key_func=get_remote_address, default_limits=["100 per minute", "5 per second"]
)

sitemap = Sitemap()
csrf = CSRFProtect()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    from .models import db

    bootstrap.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    sitemap.init_app(app)

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    max_log_size = 10 * 1024 * 1024  # start new log file after 10 MB
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
        (HTTPStatus.FORBIDDEN, "Forbidden", "403.html"),
        (HTTPStatus.NOT_FOUND, "Not found", "404.html"),
        (HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "File too large", "413.html"),
        (HTTPStatus.TOO_MANY_REQUESTS, "Too many requests", "429.html"),
        (HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", "500.html"),
    ]
    for code, error, template in error_handlers:
        # Pass generated errorhandler function to @app.errorhandler decorator
        app.errorhandler(code)(create_errorhandler(code, error, template))

    # create jinja2 filter for titles with multiple capitals
    @app.template_filter("capfirst")
    def capfirst_filter(s):
        return s[0].capitalize() + s[1:]  # only change 1st letter

    @app.template_filter("get_age")
    def get_age_from_birth_year(birth_year):
        if birth_year:
            return int(datetime.datetime.now().year - birth_year)

    @app.template_filter("field_in_query")
    def field_in_query(form_data, field):
        """
        Determine if a field is specified in the form data, and if so return a Bootstrap
        class which will render the field accordion open.
        """
        return " in " if form_data.get(field) else ""

    @app.template_filter("markdown")
    def markdown(text):
        text = text.replace("\n", "  \n")  # make markdown not ignore new lines.
        html = bleach.clean(_markdown.markdown(text), markdown_tags, markdown_attrs)
        return Markup(html)

    # Add commands
    Migrate(
        app, db, os.path.join(os.path.dirname(__file__), "..", "migrations")
    )  # Adds 'db' command
    from .commands import (
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

    return app


app = create_app()
