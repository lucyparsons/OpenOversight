import config
import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc, func
from sqlalchemy.sql.expression import cast
from app import app
from app.models import Officer, Assignment, Image, Face
import pdb

db = SQLAlchemy(app)


def filter_by_form(form, officer_query):
    if form['name']:
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['name']))
            )
    if form['race'] in ('BLACK', 'WHITE', 'ASIAN', 'HISPANIC',
                        'PACIFIC ISLANDER'):
        officer_query = officer_query.filter(
            Officer.race.like('%%{}%%'.format(form['race']))
            )
    if form['gender'] in ('M', 'F'):
        officer_query = officer_query.filter(Officer.gender == form['gender'])


    current_year = datetime.datetime.now().year
    min_birth_year = current_year - int(form['min_age'])
    max_birth_year = current_year - int(form['max_age'])
    officer_query = officer_query.filter(db.or_(db.and_(Officer.birth_year <= min_birth_year,
                                                        Officer.birth_year >= max_birth_year),
                                                Officer.birth_year == None))

    officer_query = officer_query.join(Assignment)
    if form['badge']:
        officer_query = officer_query.filter(
                cast( Assignment.star_no, db.String ) \
                .like('%%{}%%'.format(form['badge']))
            )
    if form['rank'] =='PO':
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%PO%%'),
                   Assignment.rank.like('%%POLICE OFFICER%%'),
                   Assignment.rank == None)
            )
    if form['rank'] in ('FIELD', 'SERGEANT', 'LIEUTENANT', 'CAPTAIN',
                        'COMMANDER', 'DEP CHIEF', 'CHIEF', 'DEPUTY SUPT',
                        'SUPT OF POLICE'):
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%{}%%'.format(form['rank'])),
                   Assignment.rank == None)
            )

    # This handles the sorting upstream of pagination and pushes officers w/o tagged faces to the end of list
    officer_query = officer_query.outerjoin(Face).order_by(Face.officer_id.asc()).order_by(Officer.id.desc())
    return officer_query


def grab_officers(form):
    return filter_by_form(form, Officer.query)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
