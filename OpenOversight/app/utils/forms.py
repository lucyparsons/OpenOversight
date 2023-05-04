import datetime

from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import cast

from ...app.main.choices import GENDER_CHOICES, RACE_CHOICES
from ..models import (
    Assignment,
    Description,
    Face,
    Incident,
    Job,
    LicensePlate,
    Link,
    Location,
    Note,
    Officer,
    Salary,
    Unit,
    db,
)
from .general import get_or_create


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


def create_description(self, form):
    return Description(
        text_contents=form.text_contents.data,
        creator_id=form.creator_id.data,
        officer_id=form.officer_id.data,
        date_created=datetime.datetime.now(),
        date_updated=datetime.datetime.now(),
    )


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


def edit_officer_profile(officer, form):
    for field, data in form.data.items():
        setattr(officer, field, data)

    db.session.add(officer)
    db.session.commit()
    return officer


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
    officer_query = officer_query.options(
        selectinload(Officer.assignments_lazy)
    ).distinct()

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


def set_dynamic_default(form_field, value):
    # First we ensure no value is set already
    if not form_field.data:
        try:  # Try to use a default if there is one.
            form_field.data = value
        except AttributeError:
            pass
