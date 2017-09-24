import boto3
import datetime
import hashlib
import random
from sqlalchemy import func
from sqlalchemy.sql.expression import cast

from flask import current_app, url_for

from .models import db, Officer, Assignment, Image, Face, User, Unit, Department


def unit_choices():
    return db.session.query(Unit).all()


def dept_choices():
    return db.session.query(Department).all()


def add_new_assignment(officer_id, form):
    # Resign date should be null

    if form.unit.data:
        unit = form.unit.data.id
    else:
        unit = None

    new_assignment = Assignment(officer_id=officer_id,
                                star_no=form.star_no.data,
                                rank=form.rank.data,
                                unit=unit,
                                star_date=form.star_date.data)
    db.session.add(new_assignment)
    db.session.commit()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_random_image(image_query):
    if image_query.count() > 0:
        rand = random.randrange(0, image_query.count())
        return image_query[rand]
    else:
        return None


def serve_image(filepath):
    if 'http' in filepath:
        return filepath
    if 'static' in filepath:
        return url_for('static', filename=filepath.replace('static/', ''))


def compute_hash(data_to_hash):
    return hashlib.sha256(data_to_hash).hexdigest()


def upload_file(safe_local_path, src_filename, dest_filename):
    s3_client = boto3.client('s3')

    # Folder to store files in on S3 is first two chars of dest_filename
    s3_folder = dest_filename[0:2]
    s3_filename = dest_filename[2:]
    s3_path = '{}/{}'.format(s3_folder, s3_filename)
    s3_client.upload_file(safe_local_path,
                          current_app.config['S3_BUCKET_NAME'],
                          s3_path,
                          ExtraArgs={'ACL': 'public-read'})

    url = "https://s3-{}.amazonaws.com/{}/{}".format(
        current_app.config['AWS_DEFAULT_REGION'],
        current_app.config['S3_BUCKET_NAME'], s3_path
    )

    return url


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
                                                Officer.birth_year == None))  # noqa

    officer_query = officer_query.join(Assignment)
    if form['badge']:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String)
            .like('%%{}%%'.format(form['badge']))
        )
    if form['rank'] == 'PO':
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%PO%%'),
                   Assignment.rank.like('%%POLICE OFFICER%%'),
                   Assignment.rank == None)  # noqa
        )
    if form['rank'] in ('FIELD', 'SERGEANT', 'LIEUTENANT', 'CAPTAIN',
                        'COMMANDER', 'DEP CHIEF', 'CHIEF', 'DEPUTY SUPT',
                        'SUPT OF POLICE'):
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%{}%%'.format(form['rank'])),
                   Assignment.rank == None)  # noqa
        )

    # This handles the sorting upstream of pagination and pushes officers w/o tagged faces to the end of list
    officer_query = officer_query.outerjoin(Face).order_by(Face.officer_id.asc()).order_by(Officer.id.desc())
    return officer_query


def filter_roster(form, officer_query):
    if form['name']:
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['name']))
        )

    officer_query = officer_query.join(Assignment)
    if form['badge']:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String)
            .like('%%{}%%'.format(form['badge']))
        )

    officer_query = officer_query.outerjoin(Face) \
                                 .order_by(Face.officer_id.asc()) \
                                 .order_by(Officer.id.desc())
    return officer_query


def roster_lookup(form):
    return filter_roster(form, Officer.query)


def grab_officers(form):
    return filter_by_form(form, Officer.query)


def compute_leaderboard_stats(select_top=25):
    top_sorters = db.session.query(User, func.count(Image.user_id)) \
                            .select_from(Image).join(User) \
                            .group_by(User) \
                            .order_by(func.count(Image.user_id).desc()) \
                            .limit(select_top).all()
    top_taggers = db.session.query(User, func.count(Face.user_id)) \
                            .select_from(Face).join(User) \
                            .group_by(User) \
                            .order_by(func.count(Face.user_id).desc()) \
                            .limit(select_top).all()
    return top_sorters, top_taggers
