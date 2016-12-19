from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from . import models

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    from .models import db
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

app = create_app()
