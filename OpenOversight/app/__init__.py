from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    from .models import db
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500

    return app

app = create_app()
