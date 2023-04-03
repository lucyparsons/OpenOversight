import os

from OpenOversight.app import config


db = config["default"].SQLALCHEMY_DATABASE_URI
os.system("/usr/bin/pg_dump %s -f backup.sql" % db)
print("backup.sql created")
