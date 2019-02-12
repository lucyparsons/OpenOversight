import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from .config import config


bootstrap = Bootstrap()
mail = Mail()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

limiter = Limiter(key_func=get_remote_address,
                  default_limits=["100 per minute", "5 per second"])


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    from .models import db  # noqa

    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from .main import main as main_blueprint  # noqa
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint  # noqa
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    max_log_size = 10 * 1024 * 1024  # start new log file after 10 MB
    num_logs_to_keep = 5
    file_handler = RotatingFileHandler('/tmp/openoversight.log', 'a',
                                       max_log_size, num_logs_to_keep)

    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    )

    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('BPD Watch startup')

    # Also log when endpoints are getting hit hard
    limiter.logger.addHandler(file_handler)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500

    @app.errorhandler(429)
    def rate_exceeded(e):
        return render_template('429.html'), 429

    # create jinja2 filter for titles with multiple capitals
    @app.template_filter('capfirst')
    def capfirst_filter(s):
        return s[0].capitalize() + s[1:]  # only change 1st letter

    @app.template_filter('get_age')
    def get_age_from_birth_year(birth_year):
        if birth_year:
            return int(datetime.datetime.now().year - birth_year)

    # Add commands
    Migrate(app, db, os.path.join(os.path.dirname(__file__), '..', 'migrations'))  # Adds 'db' command
    from .commands import (make_admin_user, link_images_to_department,
                           link_officers_to_department, bulk_add_officers)
    app.cli.add_command(make_admin_user)
    app.cli.add_command(link_images_to_department)
    app.cli.add_command(link_officers_to_department)
    app.cli.add_command(bulk_add_officers)

    return app


app = create_app()
