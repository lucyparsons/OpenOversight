from datetime import datetime
from typing import Union

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from OpenOversight.app.main.forms import (
    AddOfficerForm,
    AssignmentForm,
    BrowseForm,
    EditOfficerForm,
    IncidentForm,
    TextForm,
)
from OpenOversight.app.models.database import (
    Assignment,
    Description,
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
from OpenOversight.app.utils.choices import GENDER_CHOICES, RACE_CHOICES


def if_exists_or_none(val: Union[str, None]) -> Union[str, None]:
    return val if val else None


def add_new_assignment(officer_id: int, form: AssignmentForm, user: User) -> None:
    unit_id = form.unit.data.id if form.unit.data else None

    job = Job.query.filter_by(
        department_id=form.job_title.data.department_id,
        job_title=form.job_title.data.job_title,
    ).one_or_none()

    new_assignment = Assignment(
        officer_id=officer_id,
        star_no=form.star_no.data,
        job_id=job.id,
        unit_id=unit_id,
        start_date=form.start_date.data,
        resign_date=form.resign_date.data,
        created_by=user.id,
        last_updated_by=user.id,
    )
    db.session.add(new_assignment)
    db.session.commit()


def add_officer_profile(form: AddOfficerForm, user: User) -> Officer:
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
        created_by=user.id,
        last_updated_by=user.id,
    )
    db.session.add(officer)
    db.session.commit()

    officer_unit = form.unit.data if form.unit.data else None

    assignment = Assignment(
        base_officer=officer,
        star_no=form.star_no.data,
        job_id=form.job_id.data,
        unit=officer_unit,
        start_date=form.employment_date.data,
        created_by=user.id,
        last_updated_by=user.id,
    )
    db.session.add(assignment)
    if form.links.data:
        form_links = [link for link in form.data["links"] if link["url"]]
        for link in form_links:
            li = get_or_create_link_from_form(link, user)
            officer.links.append(li)
    if form.notes.data:
        # don't try to create with a blank string
        form_notes = [n for n in form.data["notes"] if n["text_contents"]]
        for note in form_notes:
            new_note = Note(
                text_contents=note["text_contents"],
                officer=officer,
                created_by=user.id,
                last_updated_by=user.id,
            )
            db.session.add(new_note)
    if form.descriptions.data:
        # don't try to create with a blank string
        form_descriptions = [d for d in form.data["descriptions"] if d["text_contents"]]
        for description in form_descriptions:
            new_description = Description(
                text_contents=description["text_contents"],
                officer=officer,
                created_by=user.id,
                last_updated_by=user.id,
            )
            db.session.add(new_description)
    if form.salaries.data:
        # don't try to create with a blank string
        form_salaries = [s for s in form.data["salaries"] if s["salary"]]
        for salary in form_salaries:
            new_salary = Salary(
                officer=officer,
                salary=salary["salary"],
                overtime_pay=salary["overtime_pay"],
                year=salary["year"],
                is_fiscal_year=salary["is_fiscal_year"],
                created_by=user.id,
                last_updated_by=user.id,
            )
            db.session.add(new_salary)

    db.session.commit()
    return officer


def create_description(self, form: TextForm, user: User) -> Description:
    return Description(
        text_contents=form.text_contents.data,
        officer_id=form.officer_id.data,
        created_by=user.id,
        last_updated_by=user.id,
    )


def create_incident(self, form: IncidentForm, user: User) -> Incident:
    address_model = None
    officers = []
    license_plates = []
    links = []

    if "address" in form.data:
        address = form.data["address"]
        location = Location.query.filter_by(
            cross_street1=if_exists_or_none(address["cross_street1"]),
            cross_street2=if_exists_or_none(address["cross_street2"]),
            city=if_exists_or_none(address["city"]),
            state=if_exists_or_none(address["state"]),
            street_name=if_exists_or_none(address["street_name"]),
            zip_code=if_exists_or_none(address["zip_code"]),
        ).first()
        if not location:
            location = Location(
                cross_street1=if_exists_or_none(address["cross_street1"]),
                cross_street2=if_exists_or_none(address["cross_street2"]),
                city=if_exists_or_none(address["city"]),
                state=if_exists_or_none(address["state"]),
                street_name=if_exists_or_none(address["street_name"]),
                zip_code=if_exists_or_none(address["zip_code"]),
                created_by=user.id,
                last_updated_by=user.id,
            )
            db.session.add(location)
        address_model = location

    if "officers" in form.data:
        form_officers = [o for o in form.data["officers"] if o["oo_id"]]
        for officer in form_officers:
            of = db.session.get(Officer, int(officer["oo_id"]))
            if of:
                officers.append(of)

    if "license_plates" in form.data:
        form_plates = [p for p in form.data["license_plates"] if p["number"]]
        for plate in form_plates:
            lp = LicensePlate.query.filter_by(
                number=if_exists_or_none(plate["number"]),
                state=if_exists_or_none(plate["state"]),
            ).first()
            if not lp:
                lp = LicensePlate(
                    number=if_exists_or_none(plate["number"]),
                    state=if_exists_or_none(plate["state"]),
                    created_by=user.id,
                    last_updated_by=user.id,
                )
                db.session.add(lp)
            license_plates.append(lp)

    if "links" in form.data:
        form_links = [link for link in form.data["links"] if link["url"]]
        for link in form_links:
            li = get_or_create_link_from_form(link, user)
            links.append(li)

    return Incident(
        address=address_model,
        date=form.date_field.data,
        department=form.data["department"],
        description=form.data["description"],
        license_plates=license_plates,
        links=links,
        officers=officers,
        report_number=form.data["report_number"],
        time=form.time_field.data,
    )


def create_note(self, form: TextForm, user: User) -> Note:
    return Note(
        text_contents=form.text_contents.data,
        officer_id=form.officer_id.data,
        created_by=user.id,
        last_updated_by=user.id,
    )


def edit_existing_assignment(assignment, form: AssignmentForm) -> Assignment:
    assignment.star_no = form.star_no.data

    job = form.job_title.data
    assignment.job_id = job.id

    if form.unit.data:
        officer_unit = form.unit.data.id
    else:
        officer_unit = None

    assignment.unit_id = officer_unit
    assignment.start_date = form.start_date.data
    assignment.resign_date = form.resign_date.data
    db.session.add(assignment)
    db.session.commit()
    return assignment


def get_or_create_link_from_form(link_form, user: User) -> Union[Link, None]:
    link = None
    if link_form["url"]:
        link = Link.query.filter_by(
            author=if_exists_or_none(link_form["author"]),
            link_type=if_exists_or_none(link_form["link_type"]),
            title=if_exists_or_none(link_form["title"]),
            url=if_exists_or_none(link_form["url"]),
        ).first()
        if not link:
            link = Link(
                author=if_exists_or_none(link_form["author"]),
                description=if_exists_or_none(link_form["description"]),
                link_type=if_exists_or_none(link_form["link_type"]),
                title=if_exists_or_none(link_form["title"]),
                url=if_exists_or_none(link_form["url"]),
                has_content_warning=link_form["has_content_warning"],
                created_by=user.id,
                last_updated_by=user.id,
            )
            db.session.add(link)
    return link


def edit_officer_profile(officer, form: EditOfficerForm) -> Officer:
    for field, data in form.data.items():
        setattr(officer, field, data)

    db.session.add(officer)
    db.session.commit()
    return officer


def filter_by_form(form_data: BrowseForm, officer_query, department_id=None):
    if form_data.get("last_name"):
        officer_query = officer_query.filter(
            Officer.last_name.ilike(f"%%{form_data['last_name']}%%")
        )
    if form_data.get("first_name"):
        officer_query = officer_query.filter(
            Officer.first_name.ilike(f"%%{form_data['first_name']}%%")
        )
    if not department_id and form_data.get("dept"):
        department_id = form_data["dept"].id
        officer_query = officer_query.filter(Officer.department_id == department_id)

    if form_data.get("unique_internal_identifier"):
        officer_query = officer_query.filter(
            Officer.unique_internal_identifier.ilike(
                f"%%{form_data['unique_internal_identifier']}%%"
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
        current_year = datetime.now().year
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
            .filter(Unit.description.in_(form_data.get("unit")))
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
                Assignment.star_no.like(f"%%{form_data['badge']}%%")
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
    officer_query = officer_query.options(selectinload(Officer.assignments)).distinct()

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
