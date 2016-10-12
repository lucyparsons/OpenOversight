import config
import datetime

from flask_sqlalchemy import SQLAlchemy
from app import app
from app.models import Officer, Assignment, Image, Face
import pdb

db = SQLAlchemy(app)


def grab_officers(form):
    officer_query = db.session.query(Officer, Assignment).join(Assignment)

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

    return officer_query.all()


def grab_officer_faces(officer_ids):
    if len(officer_ids) == 0:
        return []

    officer_images = {}
    face_query = db.session.query(Image, Face).join(Face)
    for officer_id in officer_ids:
        faces = face_query.filter(Face.officer_id == officer_id).all()

        if len(faces) > 0:
            officer_images.update({officer_id: faces[0].Image.filepath})
        else:   # use placeholder image
            officer_images.update({officer_id: 'https://placehold.it/200x200'})

    return officer_images


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
