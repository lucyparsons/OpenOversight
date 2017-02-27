from sqlalchemy import *  # pragma: no cover
from migrate import *  # pragma: no cover


from migrate.changeset import schema  # pragma: no cover
pre_meta = MetaData()  # pragma: no cover
post_meta = MetaData()  # pragma: no cover
raw_images = Table('raw_images', post_meta,  # pragma: no cover
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filepath', String(length=255)),
    Column('hash_img', String(length=120)),
    Column('date_image_inserted', DateTime),
    Column('date_image_taken', DateTime),
    Column('contains_cops', Boolean),
    Column('user_id', Integer),
    Column('is_tagged', Boolean, default=ColumnDefault(False)),
)


def upgrade(migrate_engine):  # pragma: no cover
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['raw_images'].columns['filepath'].alter(type=String(255))


def downgrade(migrate_engine):  # pragma: no cover
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['raw_images'].columns['filepath'].alter(type=String(120))
