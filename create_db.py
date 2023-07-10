#!/usr/bin/python
from OpenOversight.app import create_app
from OpenOversight.app.models.database import db


app = create_app("development")
db.app = app

with app.app_context():
    db.create_all()
