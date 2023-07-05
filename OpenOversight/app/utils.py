import datetime
import hashlib
import os
import random
import sys
from distutils.util import strtobool
from io import BytesIO
from traceback import format_exc
from typing import Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import boto3
import botocore
from botocore.exceptions import ClientError
from filetype.match import image_match
from flask import current_app, url_for
from flask_login import current_user
from future.utils import iteritems
from PIL import Image as Pimage
from PIL.PngImagePlugin import PngImageFile
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import cast

from .main.choices import GENDER_CHOICES, RACE_CHOICES
from .models import (
    Assignment,
    Department,
    Description,
    Face,
    Image,
    Incident,
    Job,
    LicensePlate,
    Link,
    Location,
    Note,
    Officer,
    Salary,
    Unit,
    User,
    db,
)


# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)

# Cropped officer face image size
THUMBNAIL_SIZE = 1000, 1000


def set_dynamic_default(form_field, value):
    # First we ensure no value is set already
    if not form_field.data:
        try:  # Try to use a default if there is one.
            form_field.data = value
        except AttributeError:
            pass


def get_or_create(session, model, defaults=None, **kwargs):
    if "csrf_token" in kwargs:
        kwargs.pop("csrf_token")

    # Because id is a keyword in Python, officers member is called oo_id
    if "oo_id" in kwargs:
        kwargs = {"id": kwargs["oo_id"]}

    # We need to convert empty strings to None for filter_by
    # as '' != None in the database and
    # such that we don't create fields with empty strings instead
    # of null.
    filter_params = {}
    for key, value in kwargs.items():
        if value != "":
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
        return (
            db.session.query(Unit)
            .filter_by(department_id=department_id)
            .order_by(Unit.descrip.asc())
            .all()
        )
    return db.session.query(Unit).order_by(Unit.descrip.asc()).all()


def dept_choices():
    return db.session.query(Department).all()


def add_new_assignment(officer_id, form):
    if form.unit.data:
        unit_id = form.unit.data.id
    else:
        unit_id = None

    job = Job.query.filter_by(
        department_id=form.job_title.data.department_id,
        job_title=form.job_title.data.job_title,
    ).one_or_none()

    new_assignment = Assignment(
        officer_id=officer_id,
        star_no=form.star_no.data,
        job_id=job.id,
        unit_id=unit_id,
        star_date=form.star_date.data,
        resign_date=form.resign_date.data,
    )
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
    officer = Officer(
        first_name=form.first_name.data,
        last_name=form.last_name.data,
        middle_initial=form.middle_initial.data,
        suffix=form.suffix.data,
        race=form.race.data,
        gender=form.gender.data,
        birth_year=form.birth_year.data,
        employment_date=form.employment_date.data,
        department_id=form.department.data.id,
    )
    db.session.add(officer)
    db.session.commit()

    if form.unit.data:
        officer_unit = form.unit.data
    else:
        officer_unit = None

    assignment = Assignment(
        baseofficer=officer,
        star_no=form.star_no.data,
        job_id=form.job_id.data,
        unit=officer_unit,
        star_date=form.employment_date.data,
    )
    db.session.add(assignment)
    if form.links.data:
        for link in form.data["links"]:
            # don't try to create with a blank string
            if link["url"]:
                li, _ = get_or_create(db.session, Link, **link)
                if li:
                    officer.links.append(li)
    if form.notes.data:
        for note in form.data["notes"]:
            # don't try to create with a blank string
            if note["text_contents"]:
                new_note = Note(
                    note=note["text_contents"],
                    user_id=current_user.get_id(),
                    officer=officer,
                    date_created=datetime.datetime.now(),
                    date_updated=datetime.datetime.now(),
                )
                db.session.add(new_note)
    if form.descriptions.data:
        for description in form.data["descriptions"]:
            # don't try to create with a blank string
            if description["text_contents"]:
                new_description = Description(
                    description=description["text_contents"],
                    user_id=current_user.get_id(),
                    officer=officer,
                    date_created=datetime.datetime.now(),
                    date_updated=datetime.datetime.now(),
                )
                db.session.add(new_description)
    if form.salaries.data:
        for salary in form.data["salaries"]:
            # don't try to create with a blank string
            if salary["salary"]:
                new_salary = Salary(
                    officer=officer,
                    salary=salary["salary"],
                    overtime_pay=salary["overtime_pay"],
                    year=salary["year"],
                    is_fiscal_year=salary["is_fiscal_year"],
                )
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
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def get_random_image(image_query):
    if image_query.count() > 0:
        rand = random.randrange(0, image_query.count())
        return image_query[rand]
    else:
        return None


def serve_image(filepath):
    # Custom change for development. Do not replace minio with localhost in
    # automated tests since these run inside the docker container.
    if "minio" in filepath and not current_app.config.get("TESTING"):
        filepath = filepath.replace("minio", "localhost")
    if "http" in filepath:
        return filepath
    if "static" in filepath:
        return url_for("static", filename=filepath.replace("static/", "").lstrip("/"))


def compute_hash(data_to_hash):
    return hashlib.sha256(data_to_hash).hexdigest()


def upload_obj_to_s3(file_obj, dest_filename):
    s3_client = boto3.client("s3", endpoint_url=current_app.config["AWS_ENDPOINT_URL"])

    # Folder to store files in on S3 is first two chars of dest_filename
    s3_folder = dest_filename[0:2]
    s3_filename = dest_filename[2:]

    # File extension filtering is expected to have already been performed before this
    # point (see `upload_image_to_s3_and_store_in_db`)
    s3_content_type = image_match(file_obj).mime

    file_obj.seek(0)
    s3_path = "{}/{}".format(s3_folder, s3_filename)
    s3_client.upload_fileobj(
        file_obj,
        current_app.config["S3_BUCKET_NAME"],
        s3_path,
        ExtraArgs={"ContentType": s3_content_type, "ACL": "public-read"},
    )

    config = s3_client._client_config
    config.signature_version = botocore.UNSIGNED
    url = boto3.resource(
        "s3", config=config, endpoint_url=current_app.config["AWS_ENDPOINT_URL"]
    ).meta.client.generate_presigned_url(
        "get_object",
        Params={"Bucket": current_app.config["S3_BUCKET_NAME"], "Key": s3_path},
    )

    return url


def filter_by_form(form_data, officer_query, department_id=None):
    if form_data.get("last_name"):
        officer_query = officer_query.filter(
            Officer.last_name.ilike("%%{}%%".format(form_data["last_name"]))
        )
    if form_data.get("first_name"):
        officer_query = officer_query.filter(
            Officer.first_name.ilike("%%{}%%".format(form_data["first_name"]))
        )
    if not department_id and form_data.get("dept"):
        department_id = form_data["dept"].id
        officer_query = officer_query.filter(Officer.department_id == department_id)

    if form_data.get("unique_internal_identifier"):
        officer_query = officer_query.filter(
            Officer.unique_internal_identifier.ilike(
                "%%{}%%".format(form_data["unique_internal_identifier"])
            )
        )

    race_values = [x for x, _ in RACE_CHOICES]
    if form_data.get("race") and all(race in race_values for race in form_data["race"]):
        if "Not Sure" in form_data["race"]:
            form_data["race"].append(None)
        officer_query = officer_query.filter(Officer.race.in_(form_data["race"]))

    gender_values = [x for x, _ in GENDER_CHOICES]
    if form_data.get("gender") and all(
        gender in gender_values for gender in form_data["gender"]
    ):
        if "Not Sure" not in form_data["gender"]:
            officer_query = officer_query.filter(
                or_(Officer.gender.in_(form_data["gender"]), Officer.gender.is_(None))
            )

    if form_data.get("min_age") and form_data.get("max_age"):
        current_year = datetime.datetime.now().year
        min_birth_year = current_year - int(form_data["min_age"])
        max_birth_year = current_year - int(form_data["max_age"])
        officer_query = officer_query.filter(
            db.or_(
                db.and_(
                    Officer.birth_year <= min_birth_year,
                    Officer.birth_year >= max_birth_year,
                ),
                Officer.birth_year == None,  # noqa: E711
            )
        )

    job_ids = []
    if form_data.get("rank"):
        job_ids = [
            job.id
            for job in Job.query.filter_by(department_id=department_id)
            .filter(Job.job_title.in_(form_data.get("rank")))
            .all()
        ]

        if "Not Sure" in form_data["rank"]:
            form_data["rank"].append(None)

    unit_ids = []
    include_null_unit = False
    if form_data.get("unit"):
        unit_ids = [
            unit.id
            for unit in Unit.query.filter_by(department_id=department_id)
            .filter(Unit.descrip.in_(form_data.get("unit")))
            .all()
        ]

        if "Not Sure" in form_data["unit"]:
            include_null_unit = True

    if (
        form_data.get("badge")
        or unit_ids
        or include_null_unit
        or job_ids
        or form_data.get("current_job")
    ):
        officer_query = officer_query.join(Officer.assignments)
        if form_data.get("badge"):
            officer_query = officer_query.filter(
                Assignment.star_no.like("%%{}%%".format(form_data["badge"]))
            )

        if unit_ids or include_null_unit:
            # Split into 2 expressions because the SQL IN keyword does not match NULLs
            unit_filters = []
            if unit_ids:
                unit_filters.append(Assignment.unit_id.in_(unit_ids))
            if include_null_unit:
                unit_filters.append(Assignment.unit_id.is_(None))
            officer_query = officer_query.filter(or_(*unit_filters))

        if job_ids:
            officer_query = officer_query.filter(Assignment.job_id.in_(job_ids))

        if form_data.get("current_job"):
            officer_query = officer_query.filter(Assignment.resign_date.is_(None))
    officer_query = officer_query.options(selectinload(Officer.assignments_lazy))

    return officer_query


def filter_roster(form, officer_query):
    if "name" in form and form["name"]:
        officer_query = officer_query.filter(
            Officer.last_name.ilike("%%{}%%".format(form["name"]))
        )

    officer_query = officer_query.outerjoin(Assignment)
    if "badge" in form and form["badge"]:
        officer_query = officer_query.filter(
            cast(Assignment.star_no, db.String).like("%%{}%%".format(form["badge"]))
        )
    if "dept" in form and form["dept"]:
        officer_query = officer_query.filter(Officer.department_id == form["dept"].id)

    officer_query = (
        officer_query.outerjoin(Face)
        .order_by(Face.officer_id.asc())
        .order_by(Officer.id.desc())
    )
    return officer_query


def grab_officers(form):
    return filter_by_form(form, Officer.query)


def compute_leaderboard_stats(select_top=25):
    top_sorters = (
        db.session.query(User, func.count(Image.user_id))
        .select_from(Image)
        .join(User)
        .group_by(User)
        .order_by(func.count(Image.user_id).desc())
        .limit(select_top)
        .all()
    )
    top_taggers = (
        db.session.query(User, func.count(Face.user_id))
        .select_from(Face)
        .join(User)
        .group_by(User)
        .order_by(func.count(Face.user_id).desc())
        .limit(select_top)
        .all()
    )
    return top_sorters, top_taggers


def ac_can_edit_officer(officer, ac):
    if officer.department_id == ac.ac_department_id:
        return True
    return False


def add_department_query(form, current_user):
    """Limits the departments available on forms for acs"""
    if not current_user.is_administrator:
        form.department.query = Department.query.filter_by(
            id=current_user.ac_department_id
        )


def add_unit_query(form, current_user):
    if not current_user.is_administrator:
        form.unit.query = Unit.query.filter_by(
            department_id=current_user.ac_department_id
        ).order_by(Unit.descrip.asc())
    else:
        form.unit.query = Unit.query.order_by(Unit.descrip.asc()).all()


def replace_list(items, obj, attr, model, db):
    """Take a list of items, and object, the attribute of that object that needs to be
    replaced, the model corresponding the items, and the db.

    Sets the objects attribute to the list of items received. DOES NOT SAVE TO DB.
    """
    new_list = []
    if not hasattr(obj, attr):
        raise LookupError("The object does not have the {} attribute".format(attr))

    for item in items:
        new_item, _ = get_or_create(db.session, model, **item)
        new_list.append(new_item)
    setattr(obj, attr, new_list)


def create_incident(self, form):
    fields = {
        "date": form.date_field.data,
        "time": form.time_field.data,
        "officers": [],
        "license_plates": [],
        "links": [],
        "address": "",
        "creator_id": form.creator_id.data,
        "last_updated_id": form.last_updated_id.data,
    }

    if "address" in form.data:
        address, _ = get_or_create(db.session, Location, **form.data["address"])
        fields["address"] = address

    if "officers" in form.data:
        for officer in form.data["officers"]:
            if officer["oo_id"]:
                of, _ = get_or_create(db.session, Officer, **officer)
                if of:
                    fields["officers"].append(of)

    if "license_plates" in form.data:
        for plate in form.data["license_plates"]:
            if plate["number"]:
                pl, _ = get_or_create(db.session, LicensePlate, **plate)
                if pl:
                    fields["license_plates"].append(pl)

    if "links" in form.data:
        for link in form.data["links"]:
            # don't try to create with a blank string
            if link["url"]:
                li, _ = get_or_create(db.session, Link, **link)
                if li:
                    fields["links"].append(li)

    return Incident(
        date=fields["date"],
        time=fields["time"],
        description=form.data["description"],
        department=form.data["department"],
        address=fields["address"],
        officers=fields["officers"],
        report_number=form.data["report_number"],
        license_plates=fields["license_plates"],
        links=fields["links"],
        creator_id=fields["creator_id"],
        last_updated_id=fields["last_updated_id"],
    )


def create_note(self, form):
    return Note(
        text_contents=form.text_contents.data,
        creator_id=form.creator_id.data,
        officer_id=form.officer_id.data,
        date_created=datetime.datetime.now(),
        date_updated=datetime.datetime.now(),
    )


def create_description(self, form):
    return Description(
        text_contents=form.text_contents.data,
        creator_id=form.creator_id.data,
        officer_id=form.officer_id.data,
        date_created=datetime.datetime.now(),
        date_updated=datetime.datetime.now(),
    )


def crop_image(image, crop_data=None, department_id=None):
    """Crops an image to given dimensions and shrinks it to fit within a configured
    bounding box if the cropped image is still too big.
    """
    if "http" in image.filepath:
        with urlopen(image.filepath) as response:
            image_buf = BytesIO(response.read())
    else:
        image_buf = open(os.path.abspath(current_app.root_path) + image.filepath, "rb")

    pimage = Pimage.open(image_buf)

    if (
        not crop_data
        and pimage.size[0] < THUMBNAIL_SIZE[0]
        and pimage.size[1] < THUMBNAIL_SIZE[1]
    ):
        return image

    # Crops image to face and resizes to bounding box if still too big
    if crop_data:
        pimage = pimage.crop(crop_data)
    if pimage.size[0] > THUMBNAIL_SIZE[0] or pimage.size[1] > THUMBNAIL_SIZE[1]:
        pimage.thumbnail(THUMBNAIL_SIZE)

    # JPEG doesn't support alpha channel, convert to RGB
    if pimage.mode in ("RGBA", "P"):
        pimage = pimage.convert("RGB")

    # Save preview image as JPEG to save bandwidth for mobile users
    cropped_image_buf = BytesIO()
    pimage.save(cropped_image_buf, "jpeg", quality=95, optimize=True, progressive=True)

    return upload_image_to_s3_and_store_in_db(
        cropped_image_buf, current_user.get_id(), department_id
    )


def upload_image_to_s3_and_store_in_db(image_buf, user_id, department_id=None):
    """
    Just a quick explaination of the order of operations here...
    we have to scrub the image before we do anything else like hash it
    but we also have to get the date for the image before we scrub it.
    """
    kind = image_match(image_buf)
    image_type = kind.extension.lower() if kind else None
    if image_type not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Attempted to pass invalid data type: {}".format(image_type))

    # PIL expects format name to be JPEG, not JPG
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    if image_type == "jpg":
        image_type = "jpeg"

    # Scrub EXIF data, extracting date taken data if it exists
    image_buf.seek(0)
    pimage = Pimage.open(image_buf)
    date_taken = find_date_taken(pimage)
    if date_taken:
        date_taken = datetime.datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
    pimage.getexif().clear()
    scrubbed_image_buf = BytesIO()
    pimage.save(scrubbed_image_buf, image_type)
    pimage.close()

    # Check whether image with hash already exists
    scrubbed_image_buf.seek(0)
    image_data = scrubbed_image_buf.read()
    hash_img = compute_hash(image_data)
    existing_image = Image.query.filter_by(hash_img=hash_img).first()
    if existing_image:
        return existing_image

    try:
        new_filename = "{}.{}".format(hash_img, image_type)
        scrubbed_image_buf.seek(0)
        url = upload_obj_to_s3(scrubbed_image_buf, new_filename)
        new_image = Image(
            filepath=url,
            hash_img=hash_img,
            date_image_inserted=datetime.datetime.now(),
            department_id=department_id,
            date_image_taken=date_taken,
            user_id=user_id,
        )
        db.session.add(new_image)
        db.session.commit()
        return new_image
    except ClientError:
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error(
            "Error uploading to S3: {}".format(
                " ".join([str(exception_type), str(value), format_exc()])
            )
        )
        return None


def find_date_taken(pimage):
    if isinstance(pimage, PngImageFile):
        return None

    exif = hasattr(pimage, "_getexif") and pimage._getexif()
    if exif:
        # 36867 in the exif tags holds the date and the original image was taken https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif.html
        if 36867 in exif:
            return exif[36867]
    else:
        return None


def get_officer(department_id, star_no, first_name, last_name):
    """
    Return first officer with the given name and badge combo in the department, if they exist

    If star_no is None, just return the first officer with the given first and last name.
    """
    officers = Officer.query.filter_by(
        department_id=department_id, first_name=first_name, last_name=last_name
    ).all()

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
        if default is not None and choice == "":
            return strtobool(default)
        try:
            ret = strtobool(choice)
        except ValueError:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
            continue
        return ret


def normalize_gender(input_gender):
    if input_gender is None:
        return None
    normalized_genders = {
        "male": "M",
        "m": "M",
        "man": "M",
        "female": "F",
        "f": "F",
        "woman": "F",
        "nonbinary": "Other",
        "other": "Other",
    }

    return normalized_genders.get(input_gender.lower().strip())


def validate_redirect_url(url: Optional[str]) -> Optional[str]:
    """
    Check that a url does not redirect to another domain.
    :param url: the url to be checked
    :return: the url if validated, otherwise `None`
    """
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None

    return url
