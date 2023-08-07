import random
from datetime import date
from http import HTTPStatus

from flask import current_app, url_for

from OpenOversight.app.main.forms import (
    AddOfficerForm,
    AssignmentForm,
    IncidentForm,
    LicensePlateForm,
    LinkForm,
    LocationForm,
)
from OpenOversight.app.models.database import Department, Incident, Job, Officer
from OpenOversight.app.models.database_cache import (
    DB_CACHE,
    has_database_cache_entry,
    model_key,
)
from OpenOversight.app.utils.choices import GENDER_CHOICES, RACE_CHOICES, STATE_CHOICES
from OpenOversight.app.utils.constants import (
    ENCODING_UTF_8,
    KEY_DEPT_ASSIGNMENTS_LAST_UPDATED,
    KEY_DEPT_INCIDENTS_LAST_UPDATED,
    KEY_DEPT_OFFICERS_LAST_UPDATED,
)
from OpenOversight.app.utils.db import unit_choices
from OpenOversight.tests.routes.route_helpers import login_admin, process_form_data


def test_model_key(mockdata, faker):
    """Test the model key generation with multiple Model inheriting classes."""
    test_key = faker.uuid4()

    test_officer = Officer(id=faker.random_number(digits=3))
    test_officer_key = model_key(test_officer, test_key)
    DB_CACHE[test_officer_key] = 1
    assert has_database_cache_entry(test_officer, test_key)

    test_department = Department(id=faker.random_number(digits=3))
    test_department_key = model_key(test_department, test_key)
    DB_CACHE[test_department_key] = 1
    assert has_database_cache_entry(test_department, test_key)

    test_incident = Incident(id=faker.random_number(digits=3))
    test_incident_key = model_key(test_incident, test_key)
    DB_CACHE[test_incident_key] = 1
    assert has_database_cache_entry(test_incident, test_key)


def test_latest_assignment_update(mockdata, client, faker):
    with current_app.test_request_context():
        login_admin(client)
        department = Department.query.first()
        department.latest_assignment_update()
        department.latest_incident_update()
        department.latest_officer_update()

        assert has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)

        officer = Officer.query.first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        star_no = str(faker.random_number(digits=4))
        form = AssignmentForm(
            star_no=star_no,
            job_title=job.id,
            start_date=date(2019, 1, 1),
            resign_date=date(2019, 12, 31),
        )

        rv = client.post(
            url_for("main.add_assignment", officer_id=3),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new assignment" in rv.data.decode(ENCODING_UTF_8)
        assert (
            has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
            is False
        )
        assert has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)


def test_latest_incident_update(mockdata, client, faker):
    with current_app.test_request_context():
        _, user = login_admin(client)
        department = Department.query.first()
        department.latest_assignment_update()
        department.latest_incident_update()
        department.latest_officer_update()

        assert has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)

        test_date = faker.date_time()

        address_form = LocationForm(
            street_name=faker.street_address(),
            cross_street1=faker.street_address(),
            city=faker.city(),
            state=random.choice(STATE_CHOICES)[0],
            zip_code=faker.postcode(),
            created_by=user.id,
        )
        # These have to have a dropdown selected because if not, an empty Unicode
        # string is sent, which does not mach the '' selector.
        link_form = LinkForm(link_type="video", created_by=user.id)
        license_plates_form = LicensePlateForm(state="AZ", created_by=user.id)
        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number="PPP Case 92",
            description=faker.sentence(nb_words=15),
            department=department.id,
            address=address_form.data,
            links=[link_form.data],
            license_plates=[license_plates_form.data],
            officers=[],
            created_by=user.id,
            last_updated_by=user.id,
            last_updated_at=test_date,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api") + "new", data=data, follow_redirects=True
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)
        assert has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
        assert (
            has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
            is False
        )
        assert has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)


def test_latest_officer_update(mockdata, client, faker):
    with current_app.test_request_context():
        _, user = login_admin(client)
        department = Department.query.first()
        department.latest_assignment_update()
        department.latest_incident_update()
        department.latest_officer_update()

        assert has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)

        links = [
            LinkForm(url=faker.url(), link_type="link", created_by=user.id).data,
            LinkForm(url=faker.url(), link_type="video", created_by=user.id).data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        last_name = faker.last_name()
        form = AddOfficerForm(
            first_name=faker.first_name(),
            last_name=last_name,
            middle_initial=faker.random_uppercase_letter(),
            race=random.choice(RACE_CHOICES)[0],
            gender=random.choice(GENDER_CHOICES)[0],
            star_no=faker.random_number(digits=3),
            job_id=job.id,
            unit=random.choice(unit_choices()).id,
            department=department.id,
            birth_year=int(faker.year()),
            links=links,
            created_by=user.id,
        )

        rv = client.post(
            url_for("main.add_officer"),
            data=process_form_data(form.data),
            follow_redirects=True,
        )

        assert f"New Officer {last_name} added" in rv.data.decode(ENCODING_UTF_8)
        assert has_database_cache_entry(department, KEY_DEPT_ASSIGNMENTS_LAST_UPDATED)
        assert has_database_cache_entry(department, KEY_DEPT_INCIDENTS_LAST_UPDATED)
        assert (
            has_database_cache_entry(department, KEY_DEPT_OFFICERS_LAST_UPDATED)
            is False
        )
