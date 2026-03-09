from OpenOversight.app import create_app
from OpenOversight.app.models.database import db
from OpenOversight.app.utils.constants import KEY_ENV_DEV

app = create_app(KEY_ENV_DEV)
with app.app_context():
    db.app = app
    db.create_all()
