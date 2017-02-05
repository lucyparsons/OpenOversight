from sqlalchemy import *  # pragma: no cover
from migrate import *  # pragma: no cover


from migrate.changeset import schema  # pragma: no cover
pre_meta = MetaData()  # pragma: no cover
post_meta = MetaData()  # pragma: no cover
users = Table('users', post_meta,  # pragma: no cover
    Column('id', Integer, primary_key=True, nullable=False),
    Column('email', String(length=64)),
    Column('username', String(length=64)),
    Column('password_hash', String(length=128)),
    Column('confirmed', Boolean, default=ColumnDefault(False)),
    Column('is_administrator', Boolean, default=ColumnDefault(False)),
    Column('is_disabled', Boolean, default=ColumnDefault(False)),
)

raw_images = Table('raw_images', post_meta,  # pragma: no cover
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filepath', String(length=120)),
    Column('hash_img', String(length=120)),
    Column('date_image_inserted', DateTime),
    Column('date_image_taken', DateTime),
    Column('contains_cops', Boolean),
    Column('user_id', Integer),
    Column('is_tagged', Boolean, default=ColumnDefault(False)),
)

faces = Table('faces', pre_meta,  # pragma: no cover
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('officer_id', INTEGER),
    Column('img_id', INTEGER),
    Column('face_position', VARCHAR(length=120)),
)

faces = Table('faces', post_meta,  # pragma: no cover
    Column('id', Integer, primary_key=True, nullable=False),
    Column('officer_id', Integer),
    Column('img_id', Integer),
    Column('face_position_x', Integer),
    Column('face_position_y', Integer),
    Column('face_width', Integer),
    Column('face_height', Integer),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):  # pragma: no cover
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['users'].create()
    post_meta.tables['raw_images'].columns['contains_cops'].create()
    post_meta.tables['raw_images'].columns['user_id'].create()
    pre_meta.tables['faces'].columns['face_position'].drop()
    post_meta.tables['faces'].columns['face_height'].create()
    post_meta.tables['faces'].columns['face_position_x'].create()
    post_meta.tables['faces'].columns['face_position_y'].create()
    post_meta.tables['faces'].columns['face_width'].create()
    post_meta.tables['faces'].columns['user_id'].create()


def downgrade(migrate_engine):  # pragma: no cover
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['users'].drop()
    post_meta.tables['raw_images'].columns['contains_cops'].drop()
    post_meta.tables['raw_images'].columns['user_id'].drop()
    pre_meta.tables['faces'].columns['face_position'].create()
    post_meta.tables['faces'].columns['face_height'].drop()
    post_meta.tables['faces'].columns['face_position_x'].drop()
    post_meta.tables['faces'].columns['face_position_y'].drop()
    post_meta.tables['faces'].columns['face_width'].drop()
    post_meta.tables['faces'].columns['user_id'].drop()
