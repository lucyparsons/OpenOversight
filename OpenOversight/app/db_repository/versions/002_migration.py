from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
raw_images = Table('raw_images', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filepath', String(length=255)),
    Column('hash_img', String(length=120)),
    Column('date_image_inserted', DateTime),
    Column('date_image_taken', DateTime),
    Column('contains_cops', Boolean),
    Column('user_id', Integer),
    Column('is_tagged', Boolean, default=ColumnDefault(False)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['raw_images'].columns['filepath'].alter(type=String(255))


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['raw_images'].columns['filepath'].alter(type=String(120))
