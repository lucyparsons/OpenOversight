#!/usr/bin/python
import os.path

from OpenOversight.app import create_app
from OpenOversight.app.models import db

app = create_app('development')
db.app = app
db.create_all()
