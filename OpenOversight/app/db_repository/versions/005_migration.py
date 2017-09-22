from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint

from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()

departments = Table('departments', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=255), index=True, nullable=False),
    Column('short_name', String(length=100), nullable=False),
)

raw_images = Table('raw_images', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filepath', String(length=255)),
    Column('hash_img', String(length=120)),
    Column('date_image_inserted', DateTime),
    Column('date_image_taken', DateTime),
    Column('contains_cops', Boolean),
    Column('user_id', Integer),
    Column('is_tagged', Boolean, default=ColumnDefault(False)),
    Column('department_id', Integer),
)

cons = ForeignKeyConstraint([raw_images.c.department_id], [departments.c.id])

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    cons.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    cons.drop()
