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
    Column('department_id', Integer),
)

cons1 = ForeignKeyConstraint([officers.c.department_id], [departments.c.id])
cons2 = ForeignKeyConstraint([unit_types.c.department_id], [departments.c.id])


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    cons1.create()
    cons2.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    cons1.drop()
    cons2.drop()
