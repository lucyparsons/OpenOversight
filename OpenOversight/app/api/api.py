from flask import Blueprint

from OpenOversight.app.api.v1.api import v1 as v1_blueprint


api = Blueprint("api", __name__, url_prefix="/api")

api.register_blueprint(v1_blueprint)
