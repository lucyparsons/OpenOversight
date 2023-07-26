import os

from OpenOversight.app import config


db = config["default"].SQLALCHEMY_DATABASE_URI
os.system(f"/usr/bin/pg_dump {db} -f backup.sql")
print("backup.sql created")
