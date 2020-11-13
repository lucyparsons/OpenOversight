from typing import Optional

from future.utils import iteritems
from urllib.request import urlopen

from io import BytesIO

import boto3
from botocore.exceptions import ClientError
import botocore
import datetime
import hashlib
import os
import random
import sys
from traceback import format_exc
from distutils.util import strtobool

from sqlalchemy import func, or_
from sqlalchemy.sql.expression import cast, nullslast, desc
import imghdr as imghdr
from flask import current_app, url_for
from flask_login import current_user
from PIL import Image as Pimage
from PIL.PngImagePlugin import PngImageFile

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

    # We need to convert empty strings to None for filter_by
    # as '' != None in the database and
    # such that we don't create fields with empty strings instead
    # of null.
    filter_params = {}
    for key, value in kwargs.items():
        if value != '':
            filter_params.update({key: value})
        else:
            filter_params.update({key: None})

    instance = model.query.filter_by(**filter_params).first()

    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in iteritems(filter_params))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def unit_choices(department_id: Optional[int] = None):
    if department_id is not None:
        return db.session.query(Unit).filter_by(department_id=department_id).order_by(Unit.descrip.asc()).all()
    return db.session.query(Unit).order_by(Unit.descrip.asc()).all()


def dept_choices():
    return db.session.query(Department).all()


def add_new_assignment(officer_id, form):
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
                                star_date=form.star_date.data,
                                resign_date=form.resign_date.data)
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
    assignment.resign_date = form.resign_date.data
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
                      department_id=form.department.data.id,
                      unique_internal_identifier=form.unique_internal_identifier.data)
    db.session.add(officer)
    db.session.commit()

    if form.unit.data:
        officer_unit = form.unit.data
    else:
        officer_unit = None

    if form.job_id.data:
        assignment = Assignment(baseofficer=officer,
                                star_no=form.star_no.data,
                                job_id=form.job_id.data,
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
                    user_id=current_user.get_id(),
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
                    user_id=current_user.get_id(),
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
        return url_for('static', filename=filepath.replace('static/', '').lstrip('/'))


def compute_hash(data_to_hash):
    return hashlib.sha256(data_to_hash).hexdigest()


def upload_obj_to_s3(file_obj, dest_filename):
    s3_client = boto3.client('s3')

    # Folder to store files in on S3 is first two chars of dest_filename
    s3_folder = dest_filename[0:2]
    s3_filename = dest_filename[2:]
    file_ending = imghdr.what(None, h=file_obj.read())
    file_obj.seek(0)
    s3_content_type = "image/%s" % file_ending
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


def filter_by_form(form, officer_query, department_id=None, order=0):
    # Some SQL acrobatics to left join only the most recent assignment and salary per officer
    assignment_row_num_col = func.row_number().over(
        partition_by=Assignment.officer_id, order_by=Assignment.star_date.desc()
    ).label('assignment_row_num')
    assignment_subq = db.session.query(
        Assignment.officer_id,
        Assignment.job_id,
        Assignment.star_date,
        Assignment.star_no,
        Assignment.unit_id
    ).add_columns(assignment_row_num_col).from_self().filter(assignment_row_num_col == 1).subquery()
    salary_row_num_col = func.row_number().over(
        partition_by=Salary.officer_id, order_by=Salary.year.desc()
    ).label('salary_row_num')
    salary_subq = db.session.query(
        Salary.officer_id,
        Salary.salary,
        Salary.overtime_pay,
        Salary.year,
    ).add_columns(salary_row_num_col).from_self().filter(salary_row_num_col == 1).subquery()
    officer_query = officer_query.outerjoin(assignment_subq).outerjoin(salary_subq)

    if form.get('last_name'):
        officer_query = officer_query.filter(
            Officer.last_name.ilike('%%{}%%'.format(form['last_name']))
        )
    if form.get('first_name'):
        officer_query = officer_query.filter(
            Officer.first_name.ilike('%%{}%%'.format(form['first_name']))
        )
    if not department_id and form.get('dept'):
        department_id = form['dept'].id
        officer_query = officer_query.filter(
            Officer.department_id == department_id
        )
    if form.get('badge'):
        or_clauses = [
            assignment_subq.c.assignments_star_no.ilike('%%{}%%'.format(star_no.strip()))
            for star_no in form['badge'].split(',')
        ]
        officer_query = officer_query.filter(or_(*or_clauses))
    if form.get('unit'):
        officer_query = officer_query.filter(
            assignment_subq.c.assignments_unit_id == form['unit']
        )
    if form.get('unique_internal_identifier'):
        or_clauses = [
            Officer.unique_internal_identifier.ilike('%%{}%%'.format(uii.strip()))
            for uii in form['unique_internal_identifier'].split(',')
        ]
        officer_query = officer_query.filter(or_(*or_clauses))

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

    if form.get('photo') and all(photo in ['0', '1'] for photo in form['photo']):
        face_officer_ids = set([face.officer_id for face in Face.query.all()])
        if '0' in form['photo'] and '1' not in form['photo']:
            officer_query = officer_query.filter(
                Officer.id.notin_(face_officer_ids)
            )
        elif '1' in form['photo'] and '0' not in form['photo']:
            officer_query = officer_query.filter(
                Officer.id.in_(face_officer_ids)
            )

    if form.get('max_pay') and form.get('min_pay') and float(form['max_pay']) > float(form['min_pay']):
        officer_query = officer_query.filter(
            db.and_(
                salary_subq.c.salaries_salary + salary_subq.c.salaries_overtime_pay >= float(form['min_pay']),
                salary_subq.c.salaries_salary + salary_subq.c.salaries_overtime_pay <= float(form['max_pay'])
            )
        )
    elif form.get('min_pay') and float(form['min_pay']) > 0 and not form.get('max_pay'):
        officer_query = officer_query.filter(
            salary_subq.c.salaries_salary + salary_subq.c.salaries_overtime_pay >= float(form['min_pay'])
        )
    elif form.get('max_pay') and float(form['max_pay']) > 0 and not form.get('min_pay'):
        officer_query = officer_query.filter(
            salary_subq.c.salaries_salary + salary_subq.c.salaries_overtime_pay <= float(form['max_pay'])
        )

    if order == 0:  # Last name alphabetical
        officer_query = officer_query.order_by(Officer.last_name, Officer.first_name, Officer.id)
    elif order == 1:  # Rank
        officer_query = officer_query.order_by(nullslast(Job.order.desc()))
    elif order == 2:  # Total pay
        officer_query = officer_query.order_by(nullslast(desc(salary_subq.c.salaries_salary + salary_subq.c.salaries_overtime_pay)))
    elif order == 3:  # Salary
        officer_query = officer_query.order_by(nullslast(salary_subq.c.salaries_salary.desc()))
    elif order == 4:  # Overtime pay
        officer_query = officer_query.order_by(nullslast(salary_subq.c.salaries_overtime_pay.desc()))

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
            department_id=current_user.ac_department_id).order_by(Unit.descrip.asc())
    else:
        form.unit.query = Unit.query.order_by(Unit.descrip.asc()).all()


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
        'date': form.date_field.data,
        'time': form.time_field.data,
        'officers': [],
        'license_plates': [],
        'links': [],
        'address': '',
        'creator_id': form.creator_id.data,
        'last_updated_id': form.last_updated_id.data
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
        time=fields['time'],
        description=form.data['description'],
        department=form.data['department'],
        address=fields['address'],
        officers=fields['officers'],
        report_number=form.data['report_number'],
        license_plates=fields['license_plates'],
        links=fields['links'],
        creator_id=fields['creator_id'],
        last_updated_id=fields['last_updated_id'])


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


def crop_image(image, crop_data=None, department_id=None):
    if 'http' in image.filepath:
        with urlopen(image.filepath) as response:
            image_buf = BytesIO(response.read())
    else:
        image_buf = open(os.path.abspath(current_app.root_path) + image.filepath, 'rb')

    image_buf.seek(0)
    image_type = imghdr.what(image_buf)
    if not image_type:
        image_type = os.path.splitext(image.filepath)[1].lower()[1:]
        if image_type in ('jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2'):
            image_type = 'jpeg2000'
        elif image_type in ('jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi'):
            image_type = 'jpeg'
        elif image_type in ('tif', 'tiff'):
            image_type = 'tiff'
    pimage = Pimage.open(image_buf)

    SIZE = 300, 300
    if not crop_data and pimage.size[0] < SIZE[0] and pimage.size[1] < SIZE[1]:
        return image

    if crop_data:
        pimage = pimage.crop(crop_data)
    if pimage.size[0] > SIZE[0] or pimage.size[1] > SIZE[1]:
        pimage = pimage.copy()
        pimage.thumbnail(SIZE)

    cropped_image_buf = BytesIO()
    pimage.save(cropped_image_buf, image_type)

    return upload_image_to_s3_and_store_in_db(cropped_image_buf, current_user.get_id(), department_id)


def upload_image_to_s3_and_store_in_db(image_buf, user_id, department_id=None):
    image_buf.seek(0)
    image_type = imghdr.what(image_buf)
    image_data = image_buf.read()
    image_buf.seek(0)
    hash_img = compute_hash(image_data)
    existing_image = Image.query.filter_by(hash_img=hash_img).first()
    if existing_image:
        return existing_image
    date_taken = None
    if image_type in current_app.config['ALLOWED_EXTENSIONS']:
        image_buf.seek(0)
        pimage = Pimage.open(image_buf)
        date_taken = find_date_taken(pimage)
        if date_taken:
            date_taken = datetime.datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
    else:
        raise ValueError('Attempted to pass invalid data type: {}'.format(image_type))
    try:
        new_filename = '{}.{}'.format(hash_img, image_type)
        url = upload_obj_to_s3(image_buf, new_filename)
        new_image = Image(filepath=url, hash_img=hash_img,
                          date_image_inserted=datetime.datetime.now(),
                          department_id=department_id,
                          date_image_taken=date_taken,
                          user_id=user_id
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
    if isinstance(pimage, PngImageFile):
        return None

    if pimage._getexif():
        # 36867 in the exif tags holds the date and the original image was taken https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif.html
        if 36867 in pimage._getexif():
            return pimage._getexif()[36867]
    else:
        return None


def get_officer(department_id, star_no, first_name, last_name):
    """
    Returns first officer with the given name and badge combo in the department, if they exist

    If star_no is None, just return the first officer with the given first and last name.
    """
    officers = Officer.query.filter_by(department_id=department_id,
                                       first_name=first_name,
                                       last_name=last_name).all()

    if star_no is None:
        return officers[0]
    else:
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


def str_is_true(str_):
    return strtobool(str_.lower())


def prompt_yes_no(prompt, default="no"):
    if default is None:
        yn = " [y/n] "
    elif default == "yes":
        yn = " [Y/n] "
    elif default == "no":
        yn = " [y/N] "
    else:
        raise ValueError("invalid default answer: {}".format(default))

    while True:
        sys.stdout.write(prompt + yn)
        choice = input().lower()
        if default is not None and choice == '':
            return strtobool(default)
        try:
            ret = strtobool(choice)
        except ValueError:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
            continue
        return ret
