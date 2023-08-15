from datetime import date
from http import HTTPStatus

from flask import current_app, url_for

from OpenOversight.app.main.forms import AssignmentForm, DepartmentForm
from OpenOversight.app.models.database import (
    Assignment,
    Face,
    Image,
    Job,
    Officer,
    Salary,
)
from OpenOversight.app.utils.constants import FLASH_MSG_PERMANENT_REDIRECT
from OpenOversight.tests.conftest import AC_DEPT, PoliceDepartment
from OpenOversight.tests.routes.route_helpers import login_admin, login_user


def test_redirect_get_started_labeling(client, session):
    with current_app.test_request_context():
        resp_no_redirect = client.get(
            url_for("main.redirect_get_started_labeling"), follow_redirects=False
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_get_started_labeling"), follow_redirects=True
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.get_started_labeling")


def test_redirect_sort_images(client, session):
    with current_app.test_request_context():
        login_user(client)
        resp_no_redirect = client.get(
            url_for("main.redirect_sort_images", department_id=AC_DEPT),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_sort_images", department_id=AC_DEPT),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.sort_images", department_id=AC_DEPT
        )


def test_redirect_officer_profile(client, session):
    with current_app.test_request_context():
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        resp_no_redirect = client.get(
            url_for("main.redirect_officer_profile", officer_id=officer.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer.id
        )


def test_redirect_add_assignment(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        resp_no_redirect = client.post(
            url_for("main.redirect_add_assignment", officer_id=officer.id),
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for("main.redirect_add_assignment", officer_id=officer.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer.id
        )


def test_redirect_edit_assignment(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
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

        assignment = Assignment.query.filter_by(star_no="1234", job_id=job.id).first()
        job = Job.query.filter_by(
            department_id=officer.department_id, job_title="Commander"
        ).one()
        form = AssignmentForm(
            star_no="12345",
            job_title=job.id,
            start_date=date(2019, 2, 1),
            resign_date=date(2019, 11, 30),
        )

        resp_no_redirect = client.post(
            url_for(
                "main.redirect_edit_assignment",
                officer_id=officer.id,
                assignment_id=assignment.id,
            ),
            data=form.data,
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(
                "main.redirect_edit_assignment",
                officer_id=officer.id,
                assignment_id=assignment.id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.edit_assignment",
            officer_id=officer.id,
            assignment_id=assignment.id,
        )


def test_redirect_add_salary(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        resp_no_redirect = client.post(
            url_for("main.redirect_add_salary", officer_id=officer.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for("main.redirect_add_salary", officer_id=officer.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer.id
        )


def test_redirect_edit_salary(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        salary = Salary.query.filter_by(officer_id=officer.id).one()
        resp_no_redirect = client.post(
            url_for(
                "main.redirect_edit_salary", officer_id=officer.id, salary_id=salary.id
            ),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(
                "main.redirect_edit_salary", officer_id=officer.id, salary_id=salary.id
            ),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer.id
        )


def test_redirect_display_submission(client, session):
    with current_app.test_request_context():
        login_user(client)
        image = Image.query.filter_by(department_id=AC_DEPT).first()
        resp_no_redirect = client.get(
            url_for("main.redirect_display_submission", image_id=image.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_display_submission", image_id=image.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.display_submission", image_id=image.id
        )


def test_redirect_display_tag(client, session):
    with current_app.test_request_context():
        image = Image.query.filter_by(department_id=AC_DEPT).first()
        face = Face.query.filter_by(img_id=image.id).first()
        resp_no_redirect = client.get(
            url_for("main.redirect_display_tag", tag_id=face.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_display_tag", tag_id=face.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.display_tag", tag_id=face.id)


def test_redirect_classify_submission(client, session):
    with current_app.test_request_context():
        _, user = login_admin(client)
        image = Image.query.filter_by(created_by=user.id).first()
        resp_no_redirect = client.post(
            url_for(
                "main.redirect_classify_submission", image_id=image.id, contains_cops=0
            ),
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(
                "main.redirect_classify_submission", image_id=image.id, contains_cops=0
            ),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.index")


RedirectPD = PoliceDepartment("Redirect Police Department", "RPD")


def test_redirect_add_department(client, session):
    with current_app.test_request_context():
        _, user = login_admin(client)

        form = DepartmentForm(
            name=RedirectPD.name,
            short_name=RedirectPD.short_name,
            state=RedirectPD.state,
            created_by=user.id,
        )

        resp_no_redirect = client.post(
            url_for("main.redirect_add_department"),
            data=form.data,
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for("main.redirect_add_department"),
            data=form.data,
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.get_started_labeling",
        )


def test_redirect_edit_department(client, session):
    with current_app.test_request_context():
        _, user = login_admin(client)
        resp_no_redirect = client.get(
            url_for("main.redirect_edit_department", department_id=AC_DEPT),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_edit_department", department_id=AC_DEPT),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.edit_department", department_id=AC_DEPT
        )


def test_redirect_list_officer(client, session):
    with current_app.test_request_context():
        resp_no_redirect = client.get(
            url_for("main.redirect_list_officer", department_id=AC_DEPT),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_list_officer", department_id=AC_DEPT),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.list_officer", department_id=AC_DEPT
        )
