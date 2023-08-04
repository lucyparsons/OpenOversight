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
from OpenOversight.app.models.database import Department, Job, Officer, User
from OpenOversight.app.models.database_cache import has_department_cache_entry
from OpenOversight.app.utils.constants import (
    ENCODING_UTF_8,
    KEY_DEPT_TOTAL_ASSIGNMENTS,
    KEY_DEPT_TOTAL_INCIDENTS,
    KEY_DEPT_TOTAL_OFFICERS,
)
from OpenOversight.app.utils.db import unit_choices
from OpenOversight.tests.routes.route_helpers import login_admin, process_form_data


def test_total_documented_assignments(mockdata, client, faker):
    with current_app.test_request_context():
        login_admin(client)
        department = Department.query.first()
        department.total_documented_assignments()
        department.total_documented_incidents()
        department.total_documented_officers()

        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_ASSIGNMENTS)
            is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_INCIDENTS) is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_OFFICERS) is True
        )

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
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_ASSIGNMENTS)
            is False
        )


def test_total_documented_incidents(mockdata, client, faker):
    with current_app.test_request_context():
        login_admin(client)
        department = Department.query.first()
        department.total_documented_assignments()
        department.total_documented_incidents()
        department.total_documented_officers()
        user = User.query.first()

        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_ASSIGNMENTS)
            is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_INCIDENTS) is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_OFFICERS) is True
        )

        test_date = faker.date_time()

        address_form = LocationForm(
            street_name=faker.street_address(),
            cross_street1=faker.street_address(),
            city=faker.city(),
            state="IA",
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
            description="Something happened",
            department="1",
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

        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_INCIDENTS) is False
        )


def test_total_documented_officers(mockdata, client, faker):
    with current_app.test_request_context():
        login_admin(client)
        department = Department.query.first()
        department.total_documented_assignments()
        department.total_documented_incidents()
        department.total_documented_officers()
        user = User.query.filter_by(is_administrator=True).first()

        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_ASSIGNMENTS)
            is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_INCIDENTS) is True
        )
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_OFFICERS) is True
        )

        links = [
            LinkForm(url=faker.url(), link_type="link", created_by=user.id).data,
            LinkForm(url=faker.url(), link_type="video", created_by=user.id).data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        first_name = faker.first_name()
        last_name = faker.last_name()
        form = AddOfficerForm(
            first_name=first_name,
            last_name=last_name,
            middle_initial=faker.random_uppercase_letter(),
            race="WHITE",
            gender="M",
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
        assert (
            has_department_cache_entry(department.id, KEY_DEPT_TOTAL_OFFICERS) is False
        )
