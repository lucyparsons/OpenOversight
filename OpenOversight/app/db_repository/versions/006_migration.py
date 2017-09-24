from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
unit_types = Table('unit_types', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('descrip', String(length=120)),
    Column('department_id', Integer),
)

officers = Table('officers', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('last_name', String(length=120)),
    Column('first_name', String(length=120)),
    Column('middle_initial', String(length=120)),
    Column('race', String(length=120)),
    Column('gender', String(length=120)),
    Column('employment_date', DateTime),
    Column('birth_year', Integer),
    Column('pd_id', Integer),
    Column('department_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['unit_types'].columns['department_id'].create()
    post_meta.tables['officers'].columns['department_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['unit_types'].columns['department_id'].drop()
    post_meta.tables['officers'].columns['department_id'].drop()
