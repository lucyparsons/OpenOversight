import boto3
import datetime
import hashlib
import random
from sqlalchemy import func
from sqlalchemy.sql.expression import cast
import imghdr as imghdr
from flask import current_app, url_for

from .models import (db, Officer, Assignment, Image, Face, User, Unit, Department,
                     Incident, Location, LicensePlate, Link)


def set_dynamic_default(form_field, value):
    # First we ensure no value is set already
    if not form_field.data:
        try:  # Try to use a default if there is one.
            form_field.data = value
        except AttributeError:
            pass


def get_or_create(session, model, defaults=None, **kwargs):
    if 'csrf_token' in kwargs:
        kwargs.pop('csrf_token')
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


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


def edit_existing_assignment(assignment, form):
    assignment.star_no = form.star_no.data
    assignment.rank = form.rank.data

    if form.unit.data:
        officer_unit = form.unit.data.id
    else:
        officer_unit = None

    assignment.unit = officer_unit
    assignment.star_date = form.star_date.data
    db.session.add(assignment)
    db.session.commit()
    return assignment


def add_officer_profile(form):
    officer = Officer(first_name=form.first_name.data,
                      last_name=form.last_name.data,
                      middle_initial=form.middle_initial.data,
                      race=form.race.data,
                      gender=form.gender.data,
                      birth_year=form.birth_year.data,
                      employment_date=form.employment_date.data,
                      department_id=form.department.data.id)
    db.session.add(officer)

    if form.unit.data:
        officer_unit = form.unit.data.id
    else:
        officer_unit = None

    assignment = Assignment(baseofficer=officer,
                            star_no=form.star_no.data,
                            rank=form.rank.data,
                            unit=officer_unit,
                            star_date=form.employment_date.data)
    if form.links.data:
        for link in form.data['links']:
            # don't try to create with a blank string
            if link['url']:
                li, _ = get_or_create(db.session, Link, **link)
                if li:
                    officer.links.append(li)
    db.session.add(assignment)
    db.session.commit()
    return officer


def edit_officer_profile(officer, form):
    for field, data in form.data.iteritems():
        if field == 'links':
            for link in data:
                # don't try to create with a blank string
                if link['url']:
                    li, _ = get_or_create(db.session, Link, **link)
                    if li:
                        officer.links.append(li)
        else:
            setattr(officer, field, data)

    db.session.add(officer)
    db.session.commit()
    return officer


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
    s3_content_type = "image/%s" % imghdr.what(safe_local_path)
    s3_path = '{}/{}'.format(s3_folder, s3_filename)
    s3_client.upload_file(safe_local_path,
                          current_app.config['S3_BUCKET_NAME'],
                          s3_path,
                          ExtraArgs={'ContentType': s3_content_type, 'ACL': 'public-read'})

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
        officer_query = officer_query.filter(db.or_(
            Officer.race.like('%%{}%%'.format(form['race'])),
            Officer.race == 'Not Sure',  # noqa
            Officer.race == None  # noqa
        ))
    if form['gender'] in ('M', 'F'):
        officer_query = officer_query.filter(db.or_(Officer.gender == form['gender'],
                                                    Officer.gender == 'Not Sure',
                                                    Officer.gender == None))  # noqa
    if form['dept']:
        officer_query = officer_query.filter(
            Officer.department_id == form['dept'].id
        )

    current_year = datetime.datetime.now().year
    min_birth_year = current_year - int(form['min_age'])
    max_birth_year = current_year - int(form['max_age'])
    officer_query = officer_query.filter(db.or_(db.and_(Officer.birth_year <= min_birth_year,
                                                        Officer.birth_year >= max_birth_year),
                                                Officer.birth_year == None))  # noqa

    officer_query = officer_query.outerjoin(Assignment)
    if form['badge']:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String)
            .like('%%{}%%'.format(form['badge']))
        )
    if form['rank'] == 'PO':
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%PO%%'),
                   Assignment.rank.like('%%POLICE OFFICER%%'),
                   Assignment.rank == 'Not Sure')  # noqa
        )
    if form['rank'] in ('FIELD', 'SERGEANT', 'LIEUTENANT', 'CAPTAIN',
                        'COMMANDER', 'DEP CHIEF', 'CHIEF', 'DEPUTY SUPT',
                        'SUPT OF POLICE'):
        officer_query = officer_query.filter(
            db.or_(Assignment.rank.like('%%{}%%'.format(form['rank'])),
                   Assignment.rank == 'Not Sure')  # noqa
        )

    # This handles the sorting upstream of pagination and pushes officers w/o tagged faces to the end of list
    officer_query = officer_query.outerjoin(Face).order_by(Face.officer_id.asc()).order_by(Officer.id.desc())
    return officer_query


def filter_roster(form, officer_query):
    if form['name']:
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['name']))
        )

    officer_query = officer_query.outerjoin(Assignment)
    if form['badge']:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String)
            .like('%%{}%%'.format(form['badge']))
        )
    if form['dept']:
        officer_query = officer_query.filter(
            Officer.department_id == form['dept'].id
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


def ac_can_edit_officer(officer, ac):
    if officer.department_id == ac.ac_department_id:
        return True
    return False


def add_department_query(form, current_user):
    """Limits the departments available on forms for acs"""
    if not current_user.is_administrator:
        form.department.query = Department.query.filter_by(
            id=current_user.ac_department_id)


def add_unit_query(form, current_user):
    if not current_user.is_administrator:
        form.unit.query = Unit.query.filter_by(
            department_id=current_user.ac_department_id)
    else:
        form.unit.query = Unit.query.all()


def replace_list(items, obj, attr, model, db):
    """Takes a list of items, and object, the attribute of that object that needs to be replaced, the model corresponding the items, and the db

    Sets the objects attribute to the list of items received. DOES NOT SAVE TO DB.
    """
    new_list = []
    if not hasattr(obj, attr):
        raise LookupError('The object does not have the {} attribute'.format(attr))

    for item in items:
        new_item, _ = get_or_create(db.session, model, **item)
        new_list.append(new_item)
    setattr(obj, attr, new_list)


def create_incident(self, form):
    fields = {
        'date': form.datetime,
        'officers': [],
        'license_plates': [],
        'links': [],
        'address': ''
    }

    if 'address' in form.data:
        address, _ = get_or_create(db.session, Location, **form.data['address'])
        fields['address'] = address

    if 'officers' in form.data:
        for officer_id in form.data['officers']:
            if officer_id:
                of = Officer.query.filter_by(id=int(officer_id)).first()
                if of:
                    fields['officers'].append(of)

    if 'license_plates' in form.data:
        for plate in form.data['license_plates']:
            if plate['number']:
                pl, _ = get_or_create(db.session, LicensePlate, **plate)
                if pl:
                    fields['license_plates'].append(pl)

    if 'links' in form.data:
        for link in form.data['links']:
            # don't try to create with a blank string
            if link['url']:
                li, _ = get_or_create(db.session, Link, **link)
                if li:
                    fields['links'].append(li)

    return Incident(
        date=fields['date'],
        description=form.data['description'],
        department=form.data['department'],
        address=fields['address'],
        officers=fields['officers'],
        report_number=form.data['report_number'],
        license_plates=fields['license_plates'],
        links=fields['links'])
