import copy
import csv
import json
import random
import re
from datetime import date, datetime
from decimal import Decimal
from http import HTTPStatus
from io import BytesIO

import pytest
from flask import current_app, url_for
from mock import MagicMock, patch
from sqlalchemy.sql.operators import Operators
from werkzeug.test import TestResponse

from OpenOversight.app.main.forms import (
    AddOfficerForm,
    AddUnitForm,
    AssignmentForm,
    BrowseForm,
    DepartmentForm,
    EditDepartmentForm,
    EditOfficerForm,
    FindOfficerForm,
    IncidentForm,
    LicensePlateForm,
    LinkForm,
    LocationForm,
    OfficerLinkForm,
    SalaryForm,
)
from OpenOversight.app.models.database import (
    Assignment,
    Department,
    Face,
    Image,
    Incident,
    Job,
    Officer,
    Salary,
    Unit,
)
from OpenOversight.app.models.database_cache import (
    has_database_cache_entry,
    put_database_cache_entry,
)
from OpenOversight.app.utils.choices import GENDER_CHOICES, RACE_CHOICES
from OpenOversight.app.utils.constants import (
    ENCODING_UTF_8,
    KEY_DEPT_ALL_LINKS,
    KEY_DEPT_ALL_SALARIES,
)
from OpenOversight.app.utils.db import unit_choices
from OpenOversight.app.utils.forms import add_new_assignment
from OpenOversight.tests.conftest import (
    AC_DEPT,
    RANK_CHOICES_1,
    SPRINGFIELD_PD,
    PoliceDepartment,
)
from OpenOversight.tests.routes.route_helpers import (
    login_ac,
    login_admin,
    login_user,
    process_form_data,
)


@pytest.mark.parametrize(
    "route",
    [
        "/submit",
        "/labels",
        "/departments/1",
        "/officers/3",
        (
            "/complaints?officer_star=1901&officer_first_name=HUGH&officer_last_name=BUTZ&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png"
        ),
    ],
)
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.OK


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize(
    "route",
    [
        "/sort/departments/1",
        "/cop_faces/departments/1",
        "/departments/new",
        "/officers/new",
        "/units/new",
    ],
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


# POST-only routes
@pytest.mark.parametrize(
    "route",
    [
        "/officers/3/assignments/new",
    ],
)
def test_route_post_only(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_user_can_access_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(
            url_for("main.officer_profile", officer_id=3), follow_redirects=True
        )
        assert "Officer Detail" in rv.data.decode(ENCODING_UTF_8)


def test_user_can_access_officer_list(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(url_for("main.list_officer", department_id=2))

        assert "Officers" in rv.data.decode(ENCODING_UTF_8)


@pytest.mark.parametrize(
    "filter_func, has_placeholder",
    [
        # Officer without faces should have placeholder
        (Operators.__invert__, True),
        # Officer with faces should not have placeholder
        (lambda x: x, False),
    ],
)
def test_officer_appropriately_shows_placeholder(
    filter_func, has_placeholder, mockdata, client, session
):
    with current_app.test_request_context():
        officer = Officer.query.filter(filter_func(Officer.face.any())).first()
        placeholder = url_for(
            "static", filename="images/placeholder.png", _external=True
        )

        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )

        assert (placeholder in rv.data.decode(ENCODING_UTF_8)) == has_placeholder


def test_ac_can_access_admin_on_dept_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()

        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert "Admin only" in rv.data.decode(ENCODING_UTF_8)


def test_ac_cannot_access_admin_on_non_dept_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()

        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert "Admin only" not in rv.data.decode(ENCODING_UTF_8)


def test_admin_can_add_assignment(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        officer = Officer.query.filter_by(id=3).one()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no="1234",
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
        assert "2019-01-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-12-31" in rv.data.decode(ENCODING_UTF_8)
        assignment = Assignment.query.filter_by(star_no="1234", job_id=job.id).first()
        assert assignment.start_date == date(2019, 1, 1)
        assert assignment.resign_date == date(2019, 12, 31)


def test_admin_add_assignment_validation_error(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=3).one()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no="1234",
            job_title=job.id,
            start_date=date(2020, 1, 1),
            resign_date=date(2019, 12, 31),
        )

        rv = client.post(
            url_for("main.add_assignment", officer_id=3),
            data=form.data,
            follow_redirects=True,
        )

        assert "End date must come after start date." in rv.data.decode(ENCODING_UTF_8)
        assignments = Assignment.query.filter_by(star_no="1234", job_id=job.id).scalar()
        assert assignments is None


def test_ac_can_add_assignment_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no="S1234",
            job_title=job.id,
            start_date=date(2019, 1, 1),
            resign_date=date(2019, 12, 31),
        )

        rv = client.post(
            url_for("main.add_assignment", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new assignment" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-01-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-12-31" in rv.data.decode(ENCODING_UTF_8)

        # test that assignment exists in database
        assignment = Assignment.query.filter_by(
            star_no="S1234", officer_id=officer.id
        ).first()
        assert assignment.start_date == date(2019, 1, 1)
        assert assignment.resign_date == date(2019, 12, 31)


def test_ac_cannot_add_non_dept_assignment(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(star_no="1234", job_title=job.id)

        rv = client.post(
            url_for("main.add_assignment", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN
        assignments = Assignment.query.filter_by(star_no="1234", job_id=job.id).scalar()
        assert assignments is None


def test_admin_can_edit_assignment(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        officer = Officer.query.filter_by(id=3).one()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no="1234",
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
        assert "<td>1234</td>" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-01-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-12-31" in rv.data.decode(ENCODING_UTF_8)

        assignment = Assignment.query.filter_by(star_no="1234", job_id=job.id).first()
        assert assignment.start_date == date(2019, 1, 1)
        assert assignment.resign_date == date(2019, 12, 31)

        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Commander"
        ).one()
        form = AssignmentForm(
            star_no="12345",
            job_title=job.id,
            start_date=date(2019, 2, 1),
            resign_date=date(2019, 11, 30),
        )
        officer = Officer.query.filter_by(id=3).one()

        rv = client.post(
            url_for(
                "main.edit_assignment",
                officer_id=officer.id,
                assignment_id=officer.assignments[0].id,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert "Edited officer assignment" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>12345</td>" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-02-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-11-30" in rv.data.decode(ENCODING_UTF_8)

        assignment = Assignment.query.filter_by(star_no="12345", job_id=job.id).first()
        assert assignment.start_date == date(2019, 2, 1)
        assert assignment.resign_date == date(2019, 11, 30)


def test_admin_edit_assignment_validation_error(
    mockdata, client, session, officer_no_assignments
):
    with current_app.test_request_context():
        login_admin(client)

        officer = officer_no_assignments
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no="1234",
            job_title=job.id,
            start_date=date(2019, 1, 1),
            resign_date=date(2019, 12, 31),
        )

        client.post(
            url_for("main.add_assignment", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        # Attempt to set resign date to a date before the start date
        form = AssignmentForm(resign_date=date(2018, 12, 31))
        officer = Officer.query.filter_by(id=officer.id).one()

        rv = client.post(
            url_for(
                "main.edit_assignment",
                officer_id=officer.id,
                assignment_id=officer.assignments[0].id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assignment = Assignment.query.filter_by(star_no="1234", job_id=job.id).first()
        assert "End date must come after start date." in rv.data.decode(ENCODING_UTF_8)
        assert assignment.start_date == date(2019, 1, 1)
        assert assignment.resign_date == date(2019, 12, 31)


def test_ac_can_edit_officer_in_their_dept_assignment(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        star_no = "1234"
        new_star_no = "12345"
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(
            star_no=star_no,
            job_title=job.id,
            start_date=date(2019, 1, 1),
            resign_date=date(2019, 12, 31),
        )

        # Remove existing assignments
        Assignment.query.filter_by(officer_id=officer.id).delete()

        rv = client.post(
            url_for("main.add_assignment", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )
        assert "Added new assignment" in rv.data.decode(ENCODING_UTF_8)
        assert f"<td>{star_no}</td>" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-01-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-12-31" in rv.data.decode(ENCODING_UTF_8)
        assert officer.assignments[0].star_no == star_no
        assert officer.assignments[0].start_date == date(2019, 1, 1)
        assert officer.assignments[0].resign_date == date(2019, 12, 31)

        officer = Officer.query.filter_by(id=officer.id).one()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Commander"
        ).one()
        form = AssignmentForm(
            star_no=new_star_no,
            job_title=job.id,
            start_date=date(2019, 2, 1),
            resign_date=date(2019, 11, 30),
        )

        rv = client.post(
            url_for(
                "main.edit_assignment",
                officer_id=officer.id,
                assignment_id=officer.assignments[0].id,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert "Edited officer assignment" in rv.data.decode(ENCODING_UTF_8)
        assert f"<td>{new_star_no}</td>" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-02-01" in rv.data.decode(ENCODING_UTF_8)
        assert "2019-11-30" in rv.data.decode(ENCODING_UTF_8)
        assert officer.assignments[0].star_no == new_star_no
        assert officer.assignments[0].start_date == date(2019, 2, 1)
        assert officer.assignments[0].resign_date == date(2019, 11, 30)


def test_ac_cannot_edit_assignment_outside_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        star_no = "1234"
        new_star_no = "12345"
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Police Officer"
        ).one()
        form = AssignmentForm(star_no=star_no, job_title=job.id)

        # Remove existing assignments
        Assignment.query.filter_by(officer_id=officer.id).delete()

        rv = client.post(
            url_for("main.add_assignment", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )
        assert "Added new assignment" in rv.data.decode(ENCODING_UTF_8)
        assert f"<td>{star_no}</td>" in rv.data.decode(ENCODING_UTF_8)

        login_ac(client)

        officer = Officer.query.filter_by(id=officer.id).one()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Commander"
        ).one()
        form = AssignmentForm(star_no=new_star_no, job_title=job.id)

        rv = client.post(
            url_for(
                "main.edit_assignment",
                officer_id=officer.id,
                assignment_id=officer.assignments[0].id,
                form=form,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


TestPD = PoliceDepartment("Test Police Department", "TPD")


def test_admin_can_add_police_department(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_admin(client)

        form = DepartmentForm(
            name=TestPD.name,
            short_name=TestPD.short_name,
            state=TestPD.state,
        )

        rv = client.post(
            url_for("main.add_department"), data=form.data, follow_redirects=True
        )

        assert (
            f"New department {TestPD.name} in {TestPD.state} added to OpenOversight"
            in rv.data.decode(ENCODING_UTF_8)
        )

        # Check the department was added to the database
        department = Department.query.filter_by(name=TestPD.name).one()
        assert department.short_name == TestPD.short_name
        assert department.state == TestPD.state
        assert department.created_by == user.id
        assert department.last_updated_by == user.id


def test_admin_cannot_add_police_department_without_state(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        form = DepartmentForm(name=TestPD.name, short_name=TestPD.short_name, state="")
        form.validate()
        errors = form.errors

        assert len(errors.items()) == 1
        assert "state" in errors.keys()
        assert "Invalid value, must be one of: FA, AL, AK, AZ" in errors.get("state")[0]


def test_ac_cannot_add_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = DepartmentForm(
            name=TestPD.name,
            short_name=TestPD.short_name,
            state=TestPD.state,
        )

        rv = client.post(
            url_for("main.add_department"), data=form.data, follow_redirects=True
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_cannot_add_duplicate_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        form = DepartmentForm(
            name=TestPD.name,
            short_name=TestPD.short_name,
            state=TestPD.state,
        )

        rv = client.post(
            url_for("main.add_department"), data=form.data, follow_redirects=True
        )

        assert (
            f"New department {TestPD.name} in {TestPD.state} added to OpenOversight"
            in rv.data.decode(ENCODING_UTF_8)
        )

        # Try to add the same police department again
        rv = client.post(
            url_for("main.add_department"), data=form.data, follow_redirects=True
        )

        assert "already exists" in rv.data.decode(ENCODING_UTF_8)

        # Check that only one department was added to the database
        # one() method will throw exception if more than one department found
        department = Department.query.filter_by(name=TestPD.name).one()
        assert department.short_name == TestPD.short_name
        assert department.state == TestPD.state


CorrectedPD = PoliceDepartment("Corrected Police Department", "CPD")


def test_admin_can_edit_police_department(mockdata, client, session):
    with current_app.test_request_context():
        # Prevent CorrectedPD and MisspelledPD from having the same state
        MisspelledPD = PoliceDepartment(
            "Misspelled Police Department", "MPD", exclude_state=CorrectedPD.state
        )

        _, user = login_admin(client)

        misspelled_form = DepartmentForm(
            name=MisspelledPD.name,
            short_name=MisspelledPD.short_name,
            state=MisspelledPD.state,
        )

        misspelled_rv = client.post(
            url_for("main.add_department"),
            data=misspelled_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {MisspelledPD.name} in {MisspelledPD.state} added to "
            "OpenOversight" in misspelled_rv.data.decode(ENCODING_UTF_8)
        )

        department = Department.query.filter_by(
            name=MisspelledPD.name, state=MisspelledPD.state
        ).one()

        corrected_form = EditDepartmentForm(
            name=CorrectedPD.name,
            short_name=MisspelledPD.short_name,
            state=MisspelledPD.state,
        )

        corrected_rv = client.post(
            url_for("main.edit_department", department_id=department.id),
            data=corrected_form.data,
            follow_redirects=True,
        )

        assert (
            f"Department {CorrectedPD.name} in {MisspelledPD.state} edited"
            in corrected_rv.data.decode(ENCODING_UTF_8)
        )

        # Check the department with the new name is now in the database.
        corrected_department = Department.query.filter_by(name=CorrectedPD.name).one()
        assert corrected_department.short_name == MisspelledPD.short_name
        assert corrected_department.state == MisspelledPD.state
        assert corrected_department.created_by == user.id
        assert corrected_department.last_updated_by == user.id

        # Check that the old name is no longer present:
        assert Department.query.filter_by(name=MisspelledPD.name).count() == 0

        edit_state_form = EditDepartmentForm(
            name=CorrectedPD.name,
            short_name=CorrectedPD.short_name,
            state=MisspelledPD.state,
        )

        edit_state_rv = client.post(
            url_for("main.edit_department", department_id=department.id),
            data=edit_state_form.data,
            follow_redirects=True,
        )

        assert (
            f"Department {CorrectedPD.name} in {MisspelledPD.state} edited"
            in edit_state_rv.data.decode(ENCODING_UTF_8)
        )

        edit_state_department = Department.query.filter_by(name=CorrectedPD.name).one()
        assert edit_state_department.short_name == CorrectedPD.short_name
        assert edit_state_department.state == MisspelledPD.state
        # Check that the old short is no longer present:
        assert Department.query.filter_by(name=MisspelledPD.short_name).count() == 0

        edit_state_form = EditDepartmentForm(
            name=CorrectedPD.name,
            short_name=CorrectedPD.short_name,
            state=CorrectedPD.state,
        )

        edit_state_rv = client.post(
            url_for("main.edit_department", department_id=department.id),
            data=edit_state_form.data,
            follow_redirects=True,
        )

        assert (
            f"Department {CorrectedPD.name} in {CorrectedPD.state} edited"
            in edit_state_rv.data.decode(ENCODING_UTF_8)
        )

        edit_state_department = Department.query.filter_by(name=CorrectedPD.name).one()
        assert edit_state_department.short_name == CorrectedPD.short_name
        assert edit_state_department.state == CorrectedPD.state
        assert edit_state_department.last_updated_by == user.id
        assert edit_state_department.last_updated_at > edit_state_department.created_at
        # Check that the old short is no longer present:
        assert (
            Department.query.filter_by(
                name=CorrectedPD.short_name, state=MisspelledPD.state
            ).count()
            == 0
        )


def test_admin_cannot_edit_police_department_without_state(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        add_department_form = DepartmentForm(
            name=TestPD.name,
            short_name=TestPD.short_name,
            state=TestPD.state,
        )

        add_department_rv = client.post(
            url_for("main.add_department"),
            data=add_department_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {TestPD.name} in {TestPD.state} added to "
            "OpenOversight" in add_department_rv.data.decode(ENCODING_UTF_8)
        )

        without_state_form = EditDepartmentForm(
            name=TestPD.name, short_name=TestPD.short_name, state=""
        )

        without_state_form.validate()
        errors = without_state_form.errors

        assert len(errors.items()) == 1
        assert "state" in errors.keys()
        assert "Invalid value, must be one of: FA, AL, AK, AZ" in errors.get("state")[0]


def test_ac_cannot_edit_police_department(mockdata, client, session, department):
    with current_app.test_request_context():
        login_ac(client)

        form = EditDepartmentForm(
            name=CorrectedPD.name,
            short_name=CorrectedPD.short_name,
            state=CorrectedPD.state,
        )

        rv = client.post(
            url_for("main.edit_department", department_id=department.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_edit_rank_order(mockdata, client, session, department):
    with current_app.test_request_context():
        login_admin(client)
        ranks = department.jobs
        ranks_update = ranks.copy()
        original_first_rank = copy.deepcopy(ranks_update[0])
        ranks_update[0], ranks_update[1] = ranks_update[1], ranks_update[0]
        ranks_stringified = [rank.job_title for rank in ranks_update]

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_stringified,
        )
        processed_data = process_form_data(rank_change_form.data)

        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        updated_ranks = Department.query.filter_by(name=department.name).one().jobs
        assert (
            f"Department {department.name} in {department.state} edited"
            in rv.data.decode(ENCODING_UTF_8)
        )
        assert (
            updated_ranks[0].job_title == original_first_rank.job_title
            and updated_ranks[0].order != original_first_rank.order
        )


def test_admin_cannot_delete_rank_in_use(mockdata, client, session, department):
    with current_app.test_request_context():
        login_admin(client)

        ranks = department.jobs
        original_ranks = ranks.copy()
        ranks_update = RANK_CHOICES_1.copy()[:-1]

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        result = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        updated_ranks = Department.query.filter_by(name=department.name).one().jobs
        assert (
            "You attempted to delete a rank, Commander, that is still in use"
            in result.data.decode(ENCODING_UTF_8)
        )
        assert len(updated_ranks) == len(original_ranks)


def test_admin_can_delete_rank_not_in_use(mockdata, client, session, department):
    with current_app.test_request_context():
        login_admin(client)
        ranks_update = RANK_CHOICES_1.copy()
        original_ranks_length = len(ranks_update)
        ranks_update.append(
            Job(
                job_title="Temporary Rank",
                order=original_ranks_length,
                is_sworn_officer=True,
                department_id=AC_DEPT,
            )
        )

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # add a new rank
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length + 1
        )

        ranks_update = [
            job.job_title
            for job in Department.query.filter_by(name=department.name).one().jobs
        ]
        ranks_update = ranks_update[:-1]

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # delete the rank that was added
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length
        )


def test_admin_can_delete_multiple_ranks_not_in_use(
    mockdata, client, session, department
):
    with current_app.test_request_context():
        login_admin(client)

        ranks_update = RANK_CHOICES_1.copy()
        original_ranks_length = len(ranks_update)
        ranks_update.append("Temporary Rank 1")
        ranks_update.append("Temporary Rank 2")

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # add a new rank
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length + 2
        )

        ranks_update = [
            job.job_title
            for job in Department.query.filter_by(name=department.name).one().jobs
        ]
        ranks_update = ranks_update[:-2]

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # delete the rank that was added
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length
        )


def test_admin_cannot_commit_edit_that_deletes_one_rank_in_use_and_one_not_in_use_rank(
    mockdata, client, session, department
):
    with current_app.test_request_context():
        login_admin(client)

        ranks_update = RANK_CHOICES_1.copy()
        original_ranks_length = len(ranks_update)
        ranks_update.append(
            Job(
                job_title="Temporary Rank",
                order=original_ranks_length,
                is_sworn_officer=True,
                department_id=AC_DEPT,
            )
        )
        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # add a new rank
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length + 1
        )

        # attempt to delete multiple ranks
        ranks_update = [
            job.job_title
            for job in Department.query.filter_by(name=department.name).one().jobs
        ]
        ranks_update = ranks_update[:-2]

        rank_change_form = EditDepartmentForm(
            name=department.name,
            short_name=department.short_name,
            state=department.state,
            jobs=ranks_update,
        )
        processed_data = process_form_data(rank_change_form.data)

        # attempt to delete one rank in use and one rank not in use
        rv = client.post(
            url_for("main.edit_department", department_id=1),
            data=processed_data,
            follow_redirects=True,
        )

        assert (
            len(Department.query.filter_by(name=department.name).one().jobs)
            == original_ranks_length + 1
        )


ExistingPD = PoliceDepartment("Existing Police Department", "EPD")


def test_admin_can_create_department_with_same_name_in_different_state(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)

        existing_form = DepartmentForm(
            name=ExistingPD.name,
            short_name=ExistingPD.short_name,
            state=ExistingPD.state,
        )

        existing_rv = client.post(
            url_for("main.add_department"),
            data=existing_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {ExistingPD.name} in {ExistingPD.state} added to "
            "OpenOversight"
        ) in existing_rv.data.decode(ENCODING_UTF_8)

        existing_department = Department.query.filter_by(
            name=ExistingPD.name, state=ExistingPD.state
        ).one()
        assert existing_department.short_name == ExistingPD.short_name
        assert existing_department.state == ExistingPD.state

        # Make sure ExistingPD and ExistingDiffStatePD don't exist in the same state
        ExistingDiffStatePD = PoliceDepartment(
            "Existing Police Department", "EPD", exclude_state=ExistingPD.state
        )

        existing_diff_state_form = DepartmentForm(
            name=ExistingDiffStatePD.name,
            short_name=ExistingDiffStatePD.short_name,
            state=ExistingDiffStatePD.state,
        )

        existing_diff_state_rv = client.post(
            url_for("main.add_department"),
            data=existing_diff_state_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {ExistingDiffStatePD.name} in "
            f"{ExistingDiffStatePD.state} added to OpenOversight"
        ) in existing_diff_state_rv.data.decode(ENCODING_UTF_8)

        existing_diff_state_department = Department.query.filter_by(
            name=ExistingDiffStatePD.name, state=ExistingDiffStatePD.state
        ).one()
        assert existing_diff_state_department.short_name == ExistingPD.short_name
        assert existing_diff_state_department.state == ExistingDiffStatePD.state

        # Duplicate existing test
        existing_duplicate_form = DepartmentForm(
            name=ExistingPD.name,
            short_name=ExistingPD.short_name,
            state=ExistingPD.state,
        )

        existing_duplicate_rv = client.post(
            url_for("main.add_department"),
            data=existing_duplicate_form.data,
            follow_redirects=True,
        )

        assert (
            f"Department {ExistingPD.name} in {ExistingPD.state} already exists"
        ) in existing_duplicate_rv.data.decode(ENCODING_UTF_8)


def test_admin_cannot_duplicate_police_department_during_edit(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)

        existing_dep_form = DepartmentForm(
            name=ExistingPD.name,
            short_name=ExistingPD.short_name,
            state=ExistingPD.state,
        )

        existing_dep_rv = client.post(
            url_for("main.add_department"),
            data=existing_dep_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {ExistingPD.name} in {ExistingPD.state} added to "
            "OpenOversight"
        ) in existing_dep_rv.data.decode(ENCODING_UTF_8)

        NewPD = PoliceDepartment("New Police Department", "NPD", ExistingPD.state)

        new_dep_form = DepartmentForm(
            name=NewPD.name,
            short_name=NewPD.short_name,
            state=NewPD.state,
        )

        new_dep_rv = client.post(
            url_for("main.add_department"),
            data=new_dep_form.data,
            follow_redirects=True,
        )

        assert (
            f"New department {NewPD.name} in {NewPD.state} added to OpenOversight"
        ) in new_dep_rv.data.decode(ENCODING_UTF_8)

        new_department = Department.query.filter_by(name=NewPD.name).one()

        edit_form = EditDepartmentForm(
            name=ExistingPD.name, short_name="EPD2", state=ExistingPD.state
        )

        rv = client.post(
            url_for("main.edit_department", department_id=new_department.id),
            data=edit_form.data,
            follow_redirects=True,
        )

        assert (
            f"Department {ExistingPD.name} in {ExistingPD.state} already exists"
        ) in rv.data.decode(ENCODING_UTF_8)

        # make sure original department is still here
        existing_department = Department.query.filter_by(name=ExistingPD.name).one()
        assert existing_department.short_name == ExistingPD.short_name

        # make sure new department is left unchanged
        new_department = Department.query.filter_by(name="New Police Department").one()
        assert new_department.short_name == NewPD.short_name


def test_expected_dept_appears_in_submission_dept_selection(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(url_for("main.submit_data"), follow_redirects=True)

        assert SPRINGFIELD_PD.name in rv.data.decode(ENCODING_UTF_8)


def test_admin_can_add_new_officer(mockdata, client, session, department, faker):
    with current_app.test_request_context():
        _, admin = login_admin(client)

        links = [
            LinkForm(url=faker.url(), link_type="link").data,
            LinkForm(url=faker.url(), link_type="video").data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Test",
            last_name="McTesterson",
            middle_initial="T",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            department=department.id,
            birth_year=1990,
            links=links,
            notes=[{"text_contents": "note"}],
            descriptions=[{"text_contents": "description"}],
            salaries=[{"salary": "123.45", "overtime_pay": "543.21"}],
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "New Officer McTesterson added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="McTesterson").one()
        assert officer.first_name == "Test"
        assert officer.race == "WHITE"
        assert officer.gender == "M"
        assert officer.created_by == admin.id
        assert officer.last_updated_by == admin.id

        assert len(officer.assignments) == 1
        assert officer.assignments[0].star_no == "666"
        assert officer.assignments[0].created_by == admin.id
        assert officer.assignments[0].last_updated_by == admin.id

        assert len(officer.notes) == 1
        assert officer.notes[0].text_contents == "note"
        assert officer.notes[0].created_by == admin.id
        assert officer.notes[0].last_updated_by == admin.id

        assert len(officer.descriptions) == 1
        assert officer.descriptions[0].text_contents == "description"
        assert officer.descriptions[0].created_by == admin.id
        assert officer.descriptions[0].last_updated_by == admin.id

        assert len(officer.salaries) == 1
        assert officer.salaries[0].salary == Decimal("123.45")
        assert officer.salaries[0].overtime_pay == Decimal("543.21")
        assert officer.salaries[0].created_by == admin.id
        assert officer.descriptions[0].last_updated_by == admin.id


def test_admin_can_add_new_officer_with_unit(
    mockdata, client, session, department, faker
):
    with current_app.test_request_context():
        login_admin(client)

        unit = random.choice(unit_choices())
        links = [
            LinkForm(url=faker.url(), link_type="link").data,
            LinkForm(url=faker.url(), link_type="video").data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Test",
            last_name="McTesterson",
            middle_initial="T",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            unit=unit.id,
            department=department.id,
            birth_year=1990,
            links=links,
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "New Officer McTesterson added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="McTesterson").one()
        assert officer.first_name == "Test"
        assert officer.race == "WHITE"
        assert officer.gender == "M"
        assert Assignment.query.filter_by(base_officer=officer, unit=unit).one()


def test_ac_can_add_new_officer_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.filter_by(id=AC_DEPT).first()
        first_name = "Testy"
        last_name = "OTester"
        middle_initial = "R"
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name=first_name,
            last_name=last_name,
            middle_initial=middle_initial,
            race=race,
            gender=gender,
            star_no=666,
            job_id=job.id,
            department=department.id,
            birth_year=1990,
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert rv.status_code == HTTPStatus.OK
        assert f"New Officer {last_name} added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name=last_name).one()
        assert officer.first_name == first_name
        assert officer.race == race
        if gender == "Not Sure":
            assert officer.gender is None, (
                "A form input of 'Not Sure' should lead to"
                " the officer's gender being saved as NULL/None."
            )
        else:
            assert officer.gender == gender


def test_ac_can_add_new_officer_with_unit_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.filter_by(id=AC_DEPT).first()
        unit = random.choice(unit_choices(department_id=department.id))
        first_name = "Testy"
        last_name = "OTester"
        middle_initial = "R"
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name=first_name,
            last_name=last_name,
            middle_initial=middle_initial,
            race=race,
            gender=gender,
            star_no=666,
            job_id=job.id,
            department=department.id,
            unit=unit.id,
            birth_year=1990,
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert rv.status_code == HTTPStatus.OK
        assert f"New Officer {last_name} added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name=last_name).one()
        assert officer.first_name == first_name
        assert officer.race == race
        if gender == "Not Sure":
            assert officer.gender is None, (
                "A form input of 'Not Sure' should lead to"
                " the officer's gender being saved as NULL/None."
            )
        else:
            assert officer.gender == gender
        assert Assignment.query.filter_by(base_officer=officer, unit=unit).one()


def test_ac_cannot_add_new_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.except_(
            Department.query.filter_by(id=AC_DEPT)
        ).first()
        first_name = "Sam"
        last_name = "Augustus"
        middle_initial = "H"
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name=first_name,
            last_name=last_name,
            middle_initial=middle_initial,
            race=race,
            gender=gender,
            star_no=666,
            job_id=job.id,
            department=department.id,
            birth_year=1990,
        )

        data = process_form_data(form.data)

        client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        officer = Officer.query.filter_by(last_name=last_name).first()
        assert officer is None


def test_admin_can_edit_existing_officer(mockdata, client, session, department, faker):
    with current_app.test_request_context():
        login_admin(client)

        unit = random.choice(unit_choices())
        link_url0 = faker.url()
        link_url1 = faker.url()
        links = [
            LinkForm(url=link_url0, link_type="link").data,
            LinkForm(url=link_url0, link_type="video").data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Test",
            last_name="Testerinski",
            middle_initial="T",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            department=department.id,
            unit=unit.id,
            birth_year=1990,
            links=links,
        )
        data = process_form_data(form.data)

        client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        officer = Officer.query.filter_by(last_name="Testerinski").one()

        form = EditOfficerForm(last_name="Changed", links=links[:1])
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.edit_officer", officer_id=officer.id),
            data=data,
            follow_redirects=True,
        )

        assert "Officer Changed edited" in rv.data.decode(ENCODING_UTF_8)
        assert "Testerinski" not in rv.data.decode(ENCODING_UTF_8)
        assert link_url0 in rv.data.decode(ENCODING_UTF_8)
        assert link_url1 not in rv.data.decode(ENCODING_UTF_8)


def test_ac_cannot_edit_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        old_last_name = officer.last_name

        new_last_name = "Shiny"
        form = EditOfficerForm(last_name=new_last_name)

        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.edit_officer", officer_id=officer.id),
            data=data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN

        # Ensure changes were not made to database
        officer = Officer.query.filter_by(id=officer.id).one()
        assert officer.last_name == old_last_name


def test_ac_can_see_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()

        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        # Testing names doesn't work bc the way we display them varies
        assert str(officer.id) in rv.data.decode(ENCODING_UTF_8)


def test_ac_can_edit_officer_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.filter_by(id=AC_DEPT).first()
        unit = random.choice(unit_choices(department.id))
        first_name = "Testier"
        last_name = "OTester"
        middle_initial = "R"
        suffix = ""
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name=first_name,
            last_name=last_name,
            middle_initial=middle_initial,
            suffix=suffix,
            race=race,
            gender=gender,
            star_no=666,
            job_id=job.id,
            department=department.id,
            unit=unit.id,
            birth_year=1990,
        )

        data = process_form_data(form.data)

        client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        officer = Officer.query.filter_by(last_name=last_name).one()

        new_last_name = "Shiny"
        form = EditOfficerForm(
            first_name=first_name,
            last_name=new_last_name,
            suffix=suffix,
            race=race,
            gender=gender,
            department=department.id,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.edit_officer", officer_id=officer.id),
            data=data,
            follow_redirects=True,
        )

        assert f"Officer {new_last_name} edited" in rv.data.decode(ENCODING_UTF_8)
        assert last_name not in rv.data.decode(ENCODING_UTF_8)

        # Check the changes were added to the database
        officer = Officer.query.filter_by(id=officer.id).one()
        assert officer.last_name == new_last_name


def test_admin_adds_officer_without_middle_initial(
    mockdata, client, session, department
):
    with current_app.test_request_context():
        login_admin(client)

        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Test",
            last_name="McTesty",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            department=department.id,
            birth_year=1990,
        )
        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "New Officer McTesty added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="McTesty").one()
        assert officer.first_name == "Test"
        assert officer.middle_initial == ""
        assert officer.race == "WHITE"
        assert officer.gender == "M"


def test_admin_adds_officer_with_letter_in_badge_no(
    mockdata, client, session, department
):
    with current_app.test_request_context():
        login_admin(client)

        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Test",
            last_name="Testersly",
            middle_initial="T",
            race="WHITE",
            gender="M",
            star_no="T666",
            job_id=job.id,
            department=department.id,
            birth_year=1990,
        )
        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "New Officer Testersly added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="Testersly").one()
        assert officer.first_name == "Test"
        assert officer.race == "WHITE"
        assert officer.gender == "M"
        assert officer.assignments[0].star_no == "T666"


def test_admin_can_add_new_unit(mockdata, client, session, department):
    with current_app.test_request_context():
        login_admin(client)

        form = AddUnitForm(description="Test", department=department.id)

        rv = client.post(
            url_for("main.add_unit"), data=form.data, follow_redirects=True
        )

        assert "New unit" in rv.data.decode(ENCODING_UTF_8)

        # Check the unit was added to the database
        unit = Unit.query.filter_by(description="Test").one()
        assert unit.department_id == department.id


def test_ac_can_add_new_unit_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.filter_by(id=AC_DEPT).first()
        form = AddUnitForm(description="Test", department=department.id)

        rv = client.post(
            url_for("main.add_unit"), data=form.data, follow_redirects=True
        )

        assert "New unit" in rv.data.decode(ENCODING_UTF_8)

        # Check the unit was added to the database
        unit = Unit.query.filter_by(description="Test").one()
        assert unit.department_id == department.id


def test_ac_cannot_add_new_unit_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.except_(
            Department.query.filter_by(id=AC_DEPT)
        ).first()
        form = AddUnitForm(description="Test", department=department.id)

        client.post(url_for("main.add_unit"), data=form.data, follow_redirects=True)

        # Check the unit was not added to the database
        unit = Unit.query.filter_by(description="Test").first()
        assert unit is None


def test_admin_can_add_new_officer_with_suffix(
    mockdata, client, session, department, faker
):
    with current_app.test_request_context():
        login_admin(client)

        links = [
            LinkForm(url=faker.url(), link_type="link").data,
            LinkForm(url=faker.url(), link_type="video").data,
        ]
        job = Job.query.filter_by(department_id=department.id).first()
        form = AddOfficerForm(
            first_name="Testy",
            last_name="McTesty",
            middle_initial="T",
            suffix="Jr",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            department=department.id,
            birth_year=1990,
            links=links,
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "New Officer McTesty added" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="McTesty").one()
        assert officer.first_name == "Testy"
        assert officer.race == "WHITE"
        assert officer.gender == "M"
        assert officer.suffix == "Jr"


def test_ac_cannot_directly_upload_photos_of_of_non_dept_officers(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.except_(
            Department.query.filter_by(id=AC_DEPT)
        ).first()
        rv = client.post(
            url_for(
                "main.upload",
                department_id=department.id,
                officer_id=department.officers[0].id,
            )
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_officer_csv(mockdata, client, session, department, faker):
    with current_app.test_request_context():
        login_admin(client)
        links = [
            LinkForm(url=faker.url(), link_type="link").data,
        ]
        job = (
            Job.query.filter_by(department_id=department.id)
            .filter(Job.job_title != "Not Sure")
            .first()
        )
        form = AddOfficerForm(
            first_name="CKtVwe2gqhAIc",
            last_name="FVkcjigWUeUyA",
            middle_initial="T",
            suffix="Jr",
            race="WHITE",
            gender="M",
            star_no="90009",
            job_id=job.id,
            department=department.id,
            birth_year=1910,
            links=links,
        )
        # add the officer
        rv = client.post(
            url_for("main.add_officer"),
            data=process_form_data(form.data),
            follow_redirects=True,
        )
        assert "New Officer FVkcjigWUeUyA added" in rv.data.decode(ENCODING_UTF_8)

        # dump officer csv
        rv = client.get(
            url_for("main.download_dept_officers_csv", department_id=department.id),
            follow_redirects=True,
        )

        csv_data = rv.data.decode(ENCODING_UTF_8)
        csv_reader = csv.DictReader(csv_data.split("\n"))
        added_lines = [
            row for row in csv_reader if row["last name"] == form.last_name.data
        ]
        assert len(added_lines) == 1
        assert form.first_name.data == added_lines[0]["first name"]
        assert job.job_title == added_lines[0]["job title"]
        assert form.star_no.data == added_lines[0]["badge number"]


def test_assignments_csv(mockdata, client, session, department):
    with current_app.test_request_context():
        _, user = login_admin(client)
        officer = Officer.query.filter_by(department_id=department.id).first()
        job = (
            Job.query.filter_by(department_id=department.id)
            .filter(Job.job_title != "Not Sure")
            .first()
        )
        form = AssignmentForm(
            star_no="9181", job_title=job, start_date=date(2020, 6, 16)
        )
        add_new_assignment(officer.id, form, user)
        rv = client.get(
            url_for("main.download_dept_assignments_csv", department_id=department.id),
            follow_redirects=True,
        )
        csv_data = rv.data.decode(ENCODING_UTF_8)
        csv_reader = csv.DictReader(csv_data.split("\n"))
        all_rows = [row for row in csv_reader]
        for row in all_rows:
            assert (
                Officer.query.get(int(row["officer id"])).department_id == department.id
            )
        lines = [row for row in all_rows if int(row["officer id"]) == officer.id]
        assert len(lines) == 2
        assert (
            lines[0]["officer unique identifier"] == officer.unique_internal_identifier
        )
        assert (
            lines[1]["officer unique identifier"] == officer.unique_internal_identifier
        )
        new_assignment = [
            row for row in lines if row["badge number"] == form.star_no.data
        ]
        assert len(new_assignment) == 1
        assert new_assignment[0]["start date"] == str(form.start_date.data)
        assert new_assignment[0]["job title"] == job.job_title


def test_incidents_csv(mockdata, client, session, department, faker):
    with current_app.test_request_context():
        login_admin(client)

        # Delete existing incidents for chosen department
        Incident.query.filter_by(department_id=department.id).delete()

        incident_date = datetime(2000, 5, 25, 1, 45)
        report_number = "42"

        address_form = LocationForm(street_name="ABCDE", city="FGHI", state="IA")
        link_form = LinkForm(url=faker.url(), link_type="video")
        license_plates_form = LicensePlateForm(state="AZ")
        form = IncidentForm(
            date_field=str(incident_date.date()),
            time_field=str(incident_date.time()),
            report_number=report_number,
            description="Something happened",
            department=str(department.id),
            department_id=department.id,
            address=address_form.data,
            links=[link_form.data],
            license_plates=[license_plates_form.data],
            officers=[],
        )
        # add the incident
        rv = client.post(
            url_for("main.incident_api_new"),
            data=process_form_data(form.data),
            follow_redirects=True,
        )
        assert "created" in rv.data.decode(ENCODING_UTF_8)
        # dump incident csv
        rv = client.get(
            url_for("main.download_incidents_csv", department_id=department.id),
            follow_redirects=True,
        )

        # get the csv entry with matching report number
        csv = list(
            filter(
                lambda row: report_number in row,
                rv.data.decode(ENCODING_UTF_8).split("\n"),
            )
        )
        assert len(csv) == 1
        assert form.description.data in csv[0]


def test_browse_filtering_filters_bad(client, mockdata, session):
    with current_app.test_request_context():
        race_list = ["BLACK", "WHITE"]
        gender_list = ["M", "F"]
        rank_list = ["COMMANDER", "PO"]
        department_id = Department.query.first().id

        # Test that nothing incorrect appears in filtered data
        for race in race_list:
            for gender in gender_list:
                for rank in rank_list:
                    form = BrowseForm(
                        race=race, gender=gender, rank=rank, min_age=16, max_age=100
                    )

                    data = process_form_data(form.data)

                    rv = client.post(
                        url_for("main.list_officer", department_id=department_id),
                        data=data,
                        follow_redirects=True,
                    )

                    # Test that the combinations that should be filtered
                    # do not appear in the data
                    filter_list = rv.data.decode(ENCODING_UTF_8).split("<dt>Race</dt>")[
                        1:
                    ]
                    if race == "BLACK":
                        bad_substr = "<dd>White</dd>"
                    else:
                        bad_substr = "<dd>Black</dd>"
                    assert not any(bad_substr in token for token in filter_list)

                    filter_list = rv.data.decode(ENCODING_UTF_8).split(
                        "<dt>Gender</dt>"
                    )[1:]
                    if gender == "M":
                        bad_substr = "<dd>F</dd>"
                    else:
                        bad_substr = "<dd>M</dd>"
                    assert not any(bad_substr in token for token in filter_list)

                    filter_list = rv.data.decode(ENCODING_UTF_8).split("<dt>Rank</dt>")[
                        1:
                    ]
                    if rank == "Commander":
                        bad_substr = "<dd>Police Officer</dd>"
                    else:
                        bad_substr = "<dd>Commander</dd>"
                    assert not any(bad_substr in token for token in filter_list)


def test_browse_filtering_allows_good(client, mockdata, session, faker):
    with current_app.test_request_context():
        department_id = Department.query.first().id

        # Add an officer with a specific race, gender, rank and age to the first page
        login_admin(client)
        links = [
            LinkForm(url=faker.url(), link_type="link").data,
            LinkForm(url=faker.url(), link_type="video").data,
        ]
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        job = Job.query.filter_by(department_id=officer.department_id).first()
        unit = Unit.query.filter_by(department_id=officer.department_id).first()
        form = AddOfficerForm(
            first_name="A",
            last_name="A",
            middle_initial="A",
            race="WHITE",
            gender="M",
            star_no=666,
            job_id=job.id,
            unit=unit.id,
            department=department_id,
            birth_year=1990,
            links=links,
        )

        data = process_form_data(form.data)

        rv = client.post(url_for("main.add_officer"), data=data, follow_redirects=True)

        assert "A" in rv.data.decode(ENCODING_UTF_8)

        # Check the officer was added to the database
        officer = Officer.query.filter_by(last_name="A").one()
        assert officer.first_name == "A"
        assert officer.race == "WHITE"
        assert officer.gender == "M"

        # Check that added officer appears when filtering for this race, gender, rank
        # and age
        form = BrowseForm(
            race="WHITE",
            gender="M",
            rank=job.job_title,
            min_age=datetime.now().year - 1991,
            max_age=datetime.now().year - 1989,
            current_job=True,
        )

        data = process_form_data(form.data)

        rv = client.get(
            url_for("main.list_officer", department_id=department_id),
            data=data,
            follow_redirects=True,
        )

        def normalize_tokens_for_comparison(html_str: TestResponse, split_str: str):
            """Remove new lines, leading, and closing spaces between <dd> elements in
            formatted HTML."""
            parsed_list = html_str.data.decode(ENCODING_UTF_8).split(split_str)[1:]
            parsed_list = [re.sub(r"<dd>\n\s+", "<dd>", token) for token in parsed_list]
            parsed_list = [
                re.sub(r"\n\s+</dd>", "</dd>", token) for token in parsed_list
            ]
            return parsed_list

        filter_list = normalize_tokens_for_comparison(rv, "<dt>Rank</dt>")
        assert any(f"<dd>{job.job_title}</dd>" in token for token in filter_list)

        filter_list = normalize_tokens_for_comparison(rv, "<dt>Unit</dt>")
        assert any(f"<dd>{unit.description}</dd>" in token for token in filter_list)

        filter_list = normalize_tokens_for_comparison(rv, "<dt>Race</dt>")
        assert any("<dd>White</dd>" in token for token in filter_list)

        filter_list = normalize_tokens_for_comparison(rv, "<dt>Gender</dt>")
        assert any("<dd>Male</dd>" in token for token in filter_list)


def test_find_officer_redirect(client, mockdata, session):
    with current_app.test_request_context():
        department_id = Department.query.first().id
        rank = "Officer"
        unit_id = 1234
        min_age = datetime.now().year - 1991
        max_age = datetime.now().year - 1989

        # Check that added officer appears when filtering for this race, gender, rank
        # and age
        form = FindOfficerForm(
            dept=department_id,
            first_name="A",
            last_name="B",
            race="WHITE",
            gender="M",
            rank=rank,
            unit=unit_id,
            current_job=True,
            min_age=min_age,
            max_age=max_age,
        )

        data = process_form_data(form.data)

        # TODO starting with Flask 2.0 we can set
        # follow_redirects to true and assert on
        # rv.request.full_path (instead of rv.location)
        rv = client.post(
            url_for("main.get_officer"),
            data=data,
            follow_redirects=False,
        )

        # Check that the parameters are added correctly to the response url
        assert rv.status_code == HTTPStatus.FOUND, "Expected redirect."
        assert f"departments/{department_id}" in rv.location
        parameters = [
            ("first_name", "A"),
            ("last_name", "B"),
            ("race", "WHITE"),
            ("gender", "M"),
            ("rank", rank),
            ("unit", unit_id),
            ("current_job", True),
            ("min_age", min_age),
            ("max_age", max_age),
        ]
        for name, value in parameters:
            assert f"{name}={value}" in rv.location


def test_admin_can_upload_photos_of_dept_officers(
    mockdata, client, session, test_jpg_bytes_io
):
    with current_app.test_request_context():
        login_admin(client)

        data = dict(
            file=(test_jpg_bytes_io, "204Cat.png"),
        )

        department = Department.query.filter_by(id=AC_DEPT).first()
        officer = department.officers[3]
        officer_face_count = len(officer.face)

        # Filter out images that the officer is already tagged in
        officer_faces = Face.query.filter_by(officer_id=officer.id).all()
        image = Image.query.filter(
            Image.id.notin_([face.img_id for face in officer_faces])
        ).first()

        crop_mock = MagicMock(return_value=image)
        upload_mock = MagicMock(return_value=image)
        with patch(
            "OpenOversight.app.main.views.save_image_to_s3_and_db",
            upload_mock,
        ):
            with patch("OpenOversight.app.main.views.crop_image", crop_mock):
                rv = client.post(
                    url_for(
                        "main.upload",
                        department_id=department.id,
                        officer_id=officer.id,
                    ),
                    content_type="multipart/form-data",
                    data=data,
                )
                assert rv.status_code == HTTPStatus.OK
                assert b"Success" in rv.data
                # check that Face was added to database
                assert len(officer.face) == officer_face_count + 1


def test_upload_photo_sends_500_on_s3_error(
    mockdata, client, session, test_png_bytes_io
):
    with current_app.test_request_context():
        login_admin(client)

        data = dict(
            file=(test_png_bytes_io, "204Cat.png"),
        )

        department = Department.query.filter_by(id=AC_DEPT).first()
        mock = MagicMock(return_value=None)
        officer = department.officers[0]
        officer_face_count = len(officer.face)
        with patch("OpenOversight.app.main.views.save_image_to_s3_and_db", mock):
            rv = client.post(
                url_for(
                    "main.upload", department_id=department.id, officer_id=officer.id
                ),
                content_type="multipart/form-data",
                data=data,
            )
            assert rv.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            assert b"error" in rv.data
            # check that Face was not added to database
            assert len(officer.face) == officer_face_count


def test_upload_photo_sends_415_for_bad_file_type(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        data = dict(
            file=(BytesIO(b"my file contents"), "test_cop1.png"),
        )
        department = Department.query.filter_by(id=AC_DEPT).first()
        officer = department.officers[0]
        mock = MagicMock(return_value=False)
        with patch("OpenOversight.app.main.views.allowed_file", mock):
            rv = client.post(
                url_for(
                    "main.upload", department_id=department.id, officer_id=officer.id
                ),
                content_type="multipart/form-data",
                data=data,
            )
        assert rv.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
        assert b"not allowed" in rv.data


def test_user_cannot_upload_officer_photo(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        data = dict(
            file=(BytesIO(b"my file contents"), "test_cop1.png"),
        )
        department = Department.query.filter_by(id=AC_DEPT).first()
        officer = department.officers[0]
        rv = client.post(
            url_for("main.upload", department_id=department.id, officer_id=officer.id),
            content_type="multipart/form-data",
            data=data,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN
        assert b"not authorized" in rv.data


def test_ac_can_upload_photos_of_dept_officers(
    mockdata, client, session, test_png_bytes_io
):
    with current_app.test_request_context():
        login_ac(client)
        data = dict(
            file=(test_png_bytes_io, "204Cat.png"),
        )
        department = Department.query.filter_by(id=AC_DEPT).first()
        officer = department.officers[4]
        officer_face_count = len(officer.face)

        # Filter out images that the officer is already tagged in
        officer_faces = Face.query.filter_by(officer_id=officer.id).all()
        image = Image.query.filter(
            Image.id.notin_([face.img_id for face in officer_faces])
        ).first()

        crop_mock = MagicMock(return_value=image)
        upload_mock = MagicMock(return_value=image)
        with patch(
            "OpenOversight.app.main.views.save_image_to_s3_and_db",
            upload_mock,
        ):
            with patch("OpenOversight.app.main.views.crop_image", crop_mock):
                rv = client.post(
                    url_for(
                        "main.upload",
                        department_id=department.id,
                        officer_id=officer.id,
                    ),
                    content_type="multipart/form-data",
                    data=data,
                )
                assert rv.status_code == HTTPStatus.OK
                assert b"Success" in rv.data
                # check that Face was added to database
                assert len(officer.face) == officer_face_count + 1


def test_edit_officers_with_blank_uids(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        # Blank out all officer UID's
        session.execute(
            Officer.__table__.update().values(unique_internal_identifier=None)
        )
        session.commit()

        [officer1, officer2] = Officer.query.limit(2).all()
        assert officer1.unique_internal_identifier is None
        assert officer2.unique_internal_identifier is None

        form = EditOfficerForm(last_name="Changed", unique_internal_identifier="")
        data = process_form_data(form.data)

        # Edit first officer
        rv = client.post(
            url_for("main.edit_officer", officer_id=officer1.id),
            data=data,
            follow_redirects=True,
        )
        assert "Officer Changed edited" in rv.data.decode(ENCODING_UTF_8)
        assert officer1.last_name == "Changed"
        assert officer1.unique_internal_identifier is None

        # Edit second officer
        rv = client.post(
            url_for("main.edit_officer", officer_id=officer2.id),
            data=data,
            follow_redirects=True,
        )
        assert "Officer Changed edited" in rv.data.decode(ENCODING_UTF_8)
        assert officer2.last_name == "Changed"
        assert officer2.unique_internal_identifier is None


def test_admin_can_add_salary(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).first()
        cache_params = (Department(id=officer.department_id), KEY_DEPT_ALL_SALARIES)
        put_database_cache_entry(*cache_params, 1)

        assert has_database_cache_entry(*cache_params) is True

        form = SalaryForm(
            salary=123456.78,
            overtime_pay=666.66,
            year=2019,
            is_fiscal_year=False,
        )

        rv = client.post(
            url_for("main.add_salary", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$123,456.78</td>" in rv.data.decode(ENCODING_UTF_8)

        officer = Officer.query.filter(Officer.salaries.any(salary=123456.78)).first()
        assert officer is not None
        assert has_database_cache_entry(*cache_params) is False


def test_ac_can_add_salary_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = SalaryForm(
            salary=123456.78,
            overtime_pay=666.66,
            year=2019,
            is_fiscal_year=False,
        )
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()

        rv = client.post(
            url_for("main.add_salary", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$123,456.78</td>" in rv.data.decode(ENCODING_UTF_8)

        officer = Officer.query.filter(Officer.salaries.any(salary=123456.78)).first()
        assert officer is not None


def test_ac_cannot_add_non_dept_salary(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = SalaryForm(
            salary=123456.78, overtime_pay=666.66, year=2019, is_fiscal_year=False
        )
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()

        rv = client.post(
            url_for("main.add_salary", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_edit_salary(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=1).first()
        cache_params = (Department(id=officer.department_id), KEY_DEPT_ALL_SALARIES)
        put_database_cache_entry(*cache_params, 1)

        assert has_database_cache_entry(*cache_params) is True

        # Remove existing salaries
        Salary.query.filter_by(officer_id=1).delete()

        form = SalaryForm(
            salary=123456.78,
            overtime_pay=666.66,
            year=2019,
            is_fiscal_year=False,
        )

        rv = client.post(
            url_for("main.add_salary", officer_id=1),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$123,456.78</td>" in rv.data.decode(ENCODING_UTF_8)

        form = SalaryForm(salary=150000)
        officer = Officer.query.filter_by(id=1).one()

        rv = client.post(
            url_for(
                "main.edit_salary",
                officer_id=1,
                salary_id=officer.salaries[0].id,
                form=form,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert "Edited officer salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$150,000.00</td>" in rv.data.decode(ENCODING_UTF_8)

        officer = Officer.query.filter_by(id=1).one()
        assert officer.salaries[0].salary == 150000
        assert has_database_cache_entry(*cache_params) is False


def test_ac_can_edit_salary_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        officer_id = officer.id

        Salary.query.filter_by(officer_id=officer_id).delete()

        form = SalaryForm(
            salary=123456.78,
            overtime_pay=666.66,
            year=2019,
            is_fiscal_year=False,
        )

        rv = client.post(
            url_for("main.add_salary", officer_id=officer_id),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$123,456.78</td>" in rv.data.decode(ENCODING_UTF_8)

        form = SalaryForm(salary=150000)
        officer = Officer.query.filter_by(id=officer_id).one()

        rv = client.post(
            url_for(
                "main.edit_salary",
                officer_id=officer_id,
                salary_id=officer.salaries[0].id,
                form=form,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert "Edited officer salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$150,000.00</td>" in rv.data.decode(ENCODING_UTF_8)

        officer = Officer.query.filter_by(id=officer_id).one()
        assert officer.salaries[0].salary == 150000


def test_ac_cannot_edit_non_dept_salary(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        officer_id = officer.id

        # Remove existing salaries
        Salary.query.filter_by(officer_id=officer_id).delete()

        form = SalaryForm(
            salary=123456.78, overtime_pay=666.66, year=2019, is_fiscal_year=False
        )

        login_admin(client)
        rv = client.post(
            url_for("main.add_salary", officer_id=officer_id),
            data=form.data,
            follow_redirects=True,
        )

        assert "Added new salary" in rv.data.decode(ENCODING_UTF_8)
        assert "<td>$123,456.78</td>" in rv.data.decode(ENCODING_UTF_8)

        login_ac(client)
        form = SalaryForm(salary=150000)
        officer = Officer.query.filter_by(id=officer_id).one()

        rv = client.post(
            url_for(
                "main.edit_salary",
                officer_id=officer_id,
                salary_id=officer.salaries[0].id,
                form=form,
            ),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN

        officer = Officer.query.filter_by(id=officer_id).one()
        assert float(officer.salaries[0].salary) == 123456.78


def test_get_department_ranks_with_specific_department_id(
    mockdata, client, session, department
):
    with current_app.test_request_context():
        rv = client.get(
            url_for("main.get_dept_ranks", department_id=department.id),
            follow_redirects=True,
        )
        data = json.loads(rv.data.decode(ENCODING_UTF_8))
        data = [x[1] for x in data]
        assert "Commander" in data

        assert data.count("Commander") == 1


def test_get_department_ranks_with_no_department(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(url_for("main.get_dept_ranks"), follow_redirects=True)
        data = json.loads(rv.data.decode(ENCODING_UTF_8))
        data = [x[1] for x in data]
        assert "Commander" in data

        assert data.count("Commander") == 3  # Once for each test department


def test_admin_can_add_link_to_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        cache_params = (Department(id=officer.department_id), KEY_DEPT_ALL_LINKS)
        put_database_cache_entry(*cache_params, 1)

        assert has_database_cache_entry(*cache_params) is True

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)
        assert has_database_cache_entry(*cache_params) is False


def test_ac_can_add_link_to_officer_profile_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)


def test_ac_cannot_add_link_to_officer_profile_not_in_their_dept(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_edit_link_on_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=1).one()
        cache_params = (Department(id=officer.department_id), KEY_DEPT_ALL_LINKS)
        put_database_cache_entry(*cache_params, 1)

        assert has_database_cache_entry(*cache_params) is True
        assert len(officer.links) > 0

        link = officer.links[0]
        form = OfficerLinkForm(
            title="NEW TITLE",
            description=link.description,
            author=link.author,
            url=link.url,
            link_type=link.link_type,
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_edit", officer_id=officer.id, obj_id=link.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link successfully updated!" in rv.data.decode(ENCODING_UTF_8)
        assert "NEW TITLE" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)
        assert has_database_cache_entry(*cache_params) is False


def test_ac_can_edit_link_on_officer_profile_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        # Officer from department with id AC_DEPT and no links
        officer = (
            Officer.query.filter(
                Officer.department_id.is_(AC_DEPT),
                Officer.unique_internal_identifier.isnot(None),
            )
            .outerjoin(Officer.links)
            .filter(Officer.links == None)  # noqa: E711
            .first()
        )

        assert len(officer.links) == 0

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)

        link = officer.links[0]
        form = OfficerLinkForm(
            title="NEW TITLE",
            description=link.description,
            author=link.author,
            url=link.url,
            link_type=link.link_type,
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_edit", officer_id=officer.id, obj_id=link.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link successfully updated!" in rv.data.decode(ENCODING_UTF_8)
        assert "NEW TITLE" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)


def test_ac_cannot_edit_link_on_officer_profile_not_in_their_dept(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)
        # Officer from another department (not id AC_DEPT) and no links
        officer = (
            Officer.query.filter(
                Officer.department_id.isnot(AC_DEPT),
                Officer.unique_internal_identifier.isnot(None),
            )
            .outerjoin(Officer.links)
            .filter(Officer.links == None)  # noqa: E711
            .first()
        )

        assert len(officer.links) == 0

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)

        login_ac(client)

        link = officer.links[0]
        form = OfficerLinkForm(
            title="NEW TITLE",
            description=link.description,
            author=link.author,
            url=link.url,
            link_type=link.link_type,
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_edit", officer_id=officer.id, obj_id=link.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_delete_link_from_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        # Officer from department with id AC_DEPT and some links
        officer = (
            Officer.query.filter_by(department_id=AC_DEPT)
            .outerjoin(Officer.links)
            .filter(Officer.links is not None)
            .first()
        )
        cache_params = (Department(id=officer.department_id), KEY_DEPT_ALL_LINKS)
        put_database_cache_entry(*cache_params, 1)

        assert has_database_cache_entry(*cache_params) is True
        assert len(officer.links) > 0

        link = officer.links[0]
        rv = client.post(
            url_for("main.link_api_delete", officer_id=officer.id, obj_id=link.id),
            follow_redirects=True,
        )

        assert "link successfully deleted!" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)
        assert has_database_cache_entry(*cache_params) is False


def test_ac_can_delete_link_from_officer_profile_in_their_dept(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_ac(client)
        # Officer from department with id AC_DEPT and no links
        officer = (
            Officer.query.filter(
                Officer.department_id.is_(AC_DEPT),
                Officer.unique_internal_identifier.isnot(None),
            )
            .outerjoin(Officer.links)
            .filter(Officer.links == None)  # noqa: E711
            .first()
        )

        assert len(officer.links) == 0

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)

        link = officer.links[0]
        rv = client.post(
            url_for("main.link_api_delete", officer_id=officer.id, obj_id=link.id),
            follow_redirects=True,
        )

        assert "link successfully deleted!" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)


def test_ac_cannot_delete_link_from_officer_profile_not_in_their_dept(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)
        # Officer from another department (not id AC_DEPT) and no links
        officer = (
            Officer.query.filter(
                Officer.department_id.isnot(AC_DEPT),
                Officer.unique_internal_identifier.isnot(None),
            )
            .outerjoin(Officer.links)
            .filter(Officer.links == None)  # noqa: E711
            .first()
        )

        assert len(officer.links) == 0

        form = OfficerLinkForm(
            title="BPD Watch",
            description="Baltimore instance of OpenOversight",
            author="OJB",
            url="https://bpdwatch.com",
            link_type="link",
            officer_id=officer.id,
        )

        rv = client.post(
            url_for("main.link_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "link created!" in rv.data.decode(ENCODING_UTF_8)
        assert "BPD Watch" in rv.data.decode(ENCODING_UTF_8)
        assert officer.unique_internal_identifier in rv.data.decode(ENCODING_UTF_8)

        login_ac(client)

        link = officer.links[0]
        rv = client.post(
            url_for("main.link_api_delete", officer_id=officer.id, obj_id=link.id),
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN
