#!/usr/bin/python
from OpenOversight.app import create_app
from OpenOversight.app.models import db


app = create_app("development")
with app.app_context():
    db.app = app
    db.create_all()
