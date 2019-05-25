from future.moves.urllib.request import urlretrieve
from future.utils import iteritems

from builtins import bytes
from io import open, BytesIO

import boto3
import re
from botocore.exceptions import ClientError
import botocore
import datetime
import hashlib
import os
import random
import sys
import tempfile
from traceback import format_exc
from werkzeug import secure_filename

from sqlalchemy import func
from sqlalchemy.sql.expression import cast
import imghdr as imghdr
from flask import current_app, url_for
from PIL import Image as Pimage

from .models import (db, Officer, Assignment, Job, Image, Face, User, Unit, Department,
                     Incident, Location, LicensePlate, Link, Note, Description, Salary)
from .main.choices import RACE_CHOICES, GENDER_CHOICES

# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)


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
    # Because id is a keyword in Python, officers member is called oo_id
    if 'oo_id' in kwargs:
        kwargs = {'id': kwargs['oo_id']}
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in iteritems(kwargs))
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
        unit_id = form.unit.data.id
    else:
        unit_id = None

    job = Job.query\
             .filter_by(department_id=form.job_title.data.department_id,
                        job_title=form.job_title.data.job_title)\
             .one_or_none()

    new_assignment = Assignment(officer_id=officer_id,
                                star_no=form.star_no.data,
                                job_id=job.id,
                                unit_id=unit_id,
                                star_date=form.star_date.data)
    db.session.add(new_assignment)
    db.session.commit()


def edit_existing_assignment(assignment, form):
    assignment.star_no = form.star_no.data

    job = form.job_title.data
    assignment.job_id = job.id

    if form.unit.data:
        officer_unit = form.unit.data.id
    else:
        officer_unit = None

    assignment.unit_id = officer_unit
    assignment.star_date = form.star_date.data
    db.session.add(assignment)
    db.session.commit()
    return assignment


def add_officer_profile(form, current_user):
    officer = Officer(first_name=form.first_name.data,
                      last_name=form.last_name.data,
                      middle_initial=form.middle_initial.data,
                      suffix=form.suffix.data,
                      race=form.race.data,
                      gender=form.gender.data,
                      birth_year=form.birth_year.data,
                      employment_date=form.employment_date.data,
                      department_id=form.department.data.id)
    db.session.add(officer)
    db.session.commit()

    if form.unit.data:
        officer_unit = form.unit.data.id
    else:
        officer_unit = None

    assignment = Assignment(baseofficer=officer,
                            star_no=form.star_no.data,
                            job_id=form.job_title.data,
                            unit=officer_unit,
                            star_date=form.employment_date.data)
    db.session.add(assignment)
    if form.links.data:
        for link in form.data['links']:
            # don't try to create with a blank string
            if link['url']:
                li, _ = get_or_create(db.session, Link, **link)
                if li:
                    officer.links.append(li)
    if form.notes.data:
        for note in form.data['notes']:
            # don't try to create with a blank string
            if note['text_contents']:
                new_note = Note(
                    note=note['text_contents'],
                    user_id=current_user.id,
                    officer=officer,
                    date_created=datetime.datetime.now(),
                    date_updated=datetime.datetime.now())
                db.session.add(new_note)
    if form.descriptions.data:
        for description in form.data['descriptions']:
            # don't try to create with a blank string
            if description['text_contents']:
                new_description = Description(
                    description=description['text_contents'],
                    user_id=current_user.id,
                    officer=officer,
                    date_created=datetime.datetime.now(),
                    date_updated=datetime.datetime.now())
                db.session.add(new_description)
    if form.salaries.data:
        for salary in form.data['salaries']:
            # don't try to create with a blank string
            if salary['salary']:
                new_salary = Salary(
                    officer=officer,
                    salary=salary['salary'],
                    overtime_pay=salary['overtime_pay'],
                    year=salary['year'],
                    is_fiscal_year=salary['is_fiscal_year'])
                db.session.add(new_salary)

    db.session.commit()
    return officer


def edit_officer_profile(officer, form):
    for field, data in iteritems(form.data):
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
           ''.join(re.split(r'([.])', filename)[-2:]).lower() in current_app.config['ALLOWED_EXTENSIONS']


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
        return url_for('static', filename=filepath.replace('static/', '').lstrip('/'))


def compute_hash(data_to_hash):
    return hashlib.sha256(data_to_hash.getvalue()).hexdigest()

# def upload_file_to_s3(safe_local_path, dest_filename):
#     with open(safe_local_path, 'rb') as file_obj:
#         return upload_obj_to_s3(file_obj, dest_filename)

def upload_obj_to_s3(file_obj, dest_filename):
    s3_client = boto3.client('s3')

    # Folder to store files in on S3 is first two chars of dest_filename
    s3_folder = dest_filename[0:2]
    s3_filename = dest_filename[2:]
    s3_content_type = "image/%s" % imghdr.what(None, h=file_obj.read())
    s3_path = '{}/{}'.format(s3_folder, s3_filename)
    s3_client.upload_fileobj(file_obj,
                          current_app.config['S3_BUCKET_NAME'],
                          s3_path,
                          ExtraArgs={'ContentType': s3_content_type, 'ACL': 'public-read'})

    config = s3_client._client_config
    config.signature_version = botocore.UNSIGNED
    url = boto3.resource(
        's3', config=config).meta.client.generate_presigned_url(
        'get_object',
        Params={'Bucket': current_app.config['S3_BUCKET_NAME'],
                'Key': s3_path})

    return url


def filter_by_form(form, officer_query, department_id=None):
    # Some SQL acrobatics to left join only the most recent assignment per officer
    row_num_col = func.row_number().over(
        partition_by=Assignment.officer_id, order_by=Assignment.star_date.desc()
    ).label('row_num')
    subq = db.session.query(
        Assignment.officer_id,
        Assignment.job_id,
        Assignment.star_date,
        Assignment.star_no
    ).add_column(row_num_col).from_self().filter(row_num_col == 1).subquery()
    officer_query = officer_query.outerjoin(subq)

    if form.get('name'):
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['name']))
        )
    if not department_id and form.get('dept'):
        department_id = form['dept'].id
        officer_query = officer_query.filter(
            Officer.department_id == department_id
        )
    if form.get('badge'):
        officer_query = officer_query.filter(
            subq.c.assignments_star_no.like('%%{}%%'.format(form['badge']))
        )
    if form.get('unique_internal_identifier'):
        officer_query = officer_query.filter(
            Officer.unique_internal_identifier.ilike('%%{}%%'.format(form['unique_internal_identifier']))
        )
    race_values = [x for x, _ in RACE_CHOICES]
    if form.get('race') and all(race in race_values for race in form['race']):
        if 'Not Sure' in form['race']:
            form['race'].append(None)
        officer_query = officer_query.filter(Officer.race.in_(form['race']))
    gender_values = [x for x, _ in GENDER_CHOICES]
    if form.get('gender') and all(gender in gender_values for gender in form['gender']):
        if 'Not Sure' in form['gender']:
            form['gender'].append(None)
        officer_query = officer_query.filter(Officer.gender.in_(form['gender']))

    if form.get('min_age') and form.get('max_age'):
        current_year = datetime.datetime.now().year
        min_birth_year = current_year - int(form['min_age'])
        max_birth_year = current_year - int(form['max_age'])
        officer_query = officer_query.filter(db.or_(db.and_(Officer.birth_year <= min_birth_year,
                                                            Officer.birth_year >= max_birth_year),
                                                    Officer.birth_year == None))  # noqa

    officer_query = officer_query.outerjoin(Job, Assignment.job)
    rank_values = [x[0] for x in db.session.query(Job.job_title).filter_by(department_id=department_id, is_sworn_officer=True).all()]
    if form.get('rank') and all(rank in rank_values for rank in form['rank']):
        if 'Not Sure' in form['rank']:
            form['rank'].append(None)
        officer_query = officer_query.filter(Job.job_title.in_(form['rank']))

    return officer_query


def filter_roster(form, officer_query):
    if 'name' in form and form['name']:
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['name']))
        )

    officer_query = officer_query.outerjoin(Assignment)
    if 'badge' in form and form['badge']:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String)
            .like('%%{}%%'.format(form['badge']))
        )
    if 'dept' in form and form['dept']:
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
        for officer in form.data['officers']:
            if officer['oo_id']:
                of, _ = get_or_create(db.session, Officer, **officer)
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


def create_note(self, form):
    return Note(
        text_contents=form.text_contents.data,
        creator_id=form.creator_id.data,
        officer_id=form.officer_id.data,
        date_created=datetime.datetime.now(),
        date_updated=datetime.datetime.now())


def create_description(self, form):
    return Description(
        text_contents=form.text_contents.data,
        creator_id=form.creator_id.data,
        officer_id=form.officer_id.data,
        date_created=datetime.datetime.now(),
        date_updated=datetime.datetime.now())

def crop_image(image, crop_data, department_id):
    img_bytes = image.read()
    image_type = imghdr.what(file=image.filename, h=img_bytes)

    SIZE = 300, 300
    if crop_data:
        cropped_image = Pimage.open(img_bytes).crop(crop_data)
    else:
        cropped_image = Pimage.open(img_bytes).thumbnail(SIZE)
    with BytesIO() as img_as_bytes:
        cropped_image.save(img_as_bytes, format=image_type)
        upload_image_to_s3_and_store_in_db(img_as_bytes.getvalue(), department_id)    

def upload_image_to_s3_and_store_in_db(image_data, image_type, department_id):
    hash_img = compute_hash(image_data)    
    hash_found = Image.query.filter_by(hash_img=hash_img).first()
    if hash_found:
        return hash_found
    date_taken = None
    if image_type in current_app.config['ALLOWED_EXTENSIONS']:
        image_data.seek(0)
        image = Pimage.open(image_data)
        image_data.seek(0)
        date_taken = find_date_taken(image)
    else:
        raise ValueError('Attempted to pass invalid data type: {}'.format(image_type))
    try:
        new_filename = '{}.{}'.format(hash_img, image_type)
        url = upload_obj_to_s3(image_data, new_filename)
        new_image = Image(filepath=url, hash_img=hash_img,
                            date_image_inserted=datetime.datetime.now(),
                            department_id=department_id,
                            date_image_taken=date_taken
                            )
        db.session.add(new_image)
        db.session.commit()
        return new_image
    except ClientError:
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error uploading to S3: {}'.format(
            ' '.join([str(exception_type), str(value),
                    format_exc()])
        ))
        return None

def find_date_taken(pimage):
    if pimage.filename.split('.')[-1] == 'png':
        return None
    if pimage._getexif():
        # 36867 in the exif tags holds the date and the original image was taken https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif.html
        if 36867 in pimage._getexif():
            return pimage._getexif()[36867]
    else:
        return None


def get_officer(department_id, star_no, first_name, last_name):
    """Returns first officer with the given name and badge combo in the department, if they exist"""
    officers = Officer.query.filter_by(department_id=department_id,
                                       first_name=first_name,
                                       last_name=last_name).all()
    if officers:
        star_no = str(star_no)
        for assignment in Assignment.query.filter_by(star_no=star_no).all():
            if assignment.baseofficer in officers:
                return assignment.baseofficer
    return None


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
