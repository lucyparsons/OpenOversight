import config
import datetime

from flask_sqlalchemy import SQLAlchemy
from app import app
from app.models import Officer, Assignment, Image, Face
import pdb

db = SQLAlchemy(app)


def filter_by_form(form, officer_query):
    if form['race'] in ('BLACK', 'WHITE', 'ASIAN', 'HISPANIC', 'PACIFIC ISLANDER'):
        officer_query = officer_query.filter(Officer.race.like('%%{}%%'.format(form['race'])))
    if form['gender'] in ('M', 'F'):
        officer_query = officer_query.filter(Officer.gender == form['gender'])
    if form['rank'] =='PO':
        officer_query = officer_query.filter(db.or_(Assignment.rank.like('%%PO%%'),
                                                    Assignment.rank.like('%%POLICE OFFICER%%'),
                                                    Assignment.rank == None))
    if form['rank'] in ('FIELD', 'SERGEANT', 'LIEUTENANT', 'CAPTAIN', 'COMMANDER', 
                        'DEP CHIEF', 'CHIEF', 'DEPUTY SUPT', 'SUPT OF POLICE'):
        officer_query = officer_query.filter(db.or_(Assignment.rank.like('%%{}%%'.format(form['rank'])),
                                                    Assignment.rank == None))

    current_year = datetime.datetime.now().year
    min_birth_year = current_year - int(form['min_age'])
    max_birth_year = current_year - int(form['max_age'])
    officer_query = officer_query.filter(db.or_(db.and_(Officer.birth_year <= min_birth_year,
                                                        Officer.birth_year >= max_birth_year),
                                                Officer.birth_year == None))
    return officer_query


def grab_officers(form):
    officer_query = db.session.query(Assignment, Officer).join(Officer)
    officer_query = filter_by_form(form, officer_query)
    return officer_query.all()


def grab_officer_faces(form):
    officer_query = db.session.query(Assignment, Officer, Face, Image) \
                                    .join(Officer).join(Face).join(Image)
    officer_query = filter_by_form(form, officer_query)
    officer_images = officer_query.all()
    return officer_images


def sort_officers_by_photos(all_officers, officers_w_images):
    all_officer_ids_w_photos = [x.Officer.id for x in officers_w_images]
    all_officer_ids = [x.Officer.id for x in all_officers]

    all_officer_images = {}
    officers = officers_w_images
    for officer in officers_w_images:
        all_officer_images.update({officer.Officer.id: officer.Image.filepath})

    for officer in all_officers:
        if officer.Officer.id in all_officer_ids_w_photos:
            continue
        else:
            all_officer_images.update({officer.Officer.id: 'static/images/placeholder.png'})
            officers.append(officer)
    
    return officers, all_officer_images


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
