from app.config import config
import os

db = config['default'].SQLALCHEMY_DATABASE_URI
os.system("/usr/bin/pg_dump %s -f backup.sql" % db)
print "backup.sql created"
