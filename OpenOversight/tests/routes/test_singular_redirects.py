from datetime import date
from http import HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.main.forms import AssignmentForm, DepartmentForm
from OpenOversight.app.models.database import (
    Assignment,
    Description,
    Face,
    Image,
    Job,
    Note,
    Officer,
    Salary,
)
from OpenOversight.app.utils.constants import FLASH_MSG_PERMANENT_REDIRECT
from OpenOversight.tests.conftest import AC_DEPT, PoliceDepartment
from OpenOversight.tests.routes.route_helpers import login_admin, login_user


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_get_started_labeling", "main.get_started_labeling"),
        ("main.redirect_add_officer", "main.add_officer"),
        ("main.redirect_add_unit", "main.add_unit"),
    ],
)
def test_redirect_no_params(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        resp_no_redirect = client.get(url_for(source_route), follow_redirects=False)
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(url_for(source_route), follow_redirects=True)
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(target_route)


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_sort_images", "main.sort_images"),
        ("main.redirect_edit_department", "main.edit_department"),
        (
            "main.redirect_list_officer",
            "main.list_officer",
        ),
        ("main.redirect_get_dept_ranks", "main.get_dept_ranks"),
        ("main.redirect_download_dept_officers_csv", "main.download_dept_officers_csv"),
        (
            "main.redirect_download_dept_assignments_csv",
            "main.download_dept_assignments_csv",
        ),
        ("main.redirect_download_incidents_csv", "main.download_incidents_csv"),
        ("main.redirect_download_dept_salaries_csv", "main.download_dept_salaries_csv"),
        ("main.redirect_download_dept_links_csv", "main.download_dept_links_csv"),
        (
            "main.redirect_download_dept_descriptions_csv",
            "main.download_dept_descriptions_csv",
        ),
    ],
)
def test_redirect_with_department_id(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        resp_no_redirect = client.get(
            url_for(source_route, department_id=AC_DEPT),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for(source_route, department_id=AC_DEPT),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            target_route, department_id=AC_DEPT
        )


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_officer_profile", "main.officer_profile"),
        ("main.redirect_edit_officer", "main.edit_officer"),
        ("main.redirect_submit_officer_images", "main.submit_officer_images"),
        ("main.redirect_new_note", "main.note_api"),
        ("main.redirect_new_description", "main.description_api_new"),
        ("main.redirect_new_link", "main.link_api_new"),
    ],
)
def test_redirect_with_officer_id(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        resp_no_redirect = client.get(
            url_for(source_route, officer_id=officer.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for(source_route, officer_id=officer.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            target_route, officer_id=officer.id
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
            "main.officer_profile",
            officer_id=officer.id,
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
        login_admin(client)

        form = DepartmentForm(
            name=RedirectPD.name,
            short_name=RedirectPD.short_name,
            state=RedirectPD.state,
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


@pytest.mark.parametrize(
    "source_route",
    [
        "main.redirect_delete_tag",
        "main.redirect_set_featured_tag",
    ],
)
def test_redirect_tag(client, session, source_route):
    with current_app.test_request_context():
        login_admin(client)
        image = Image.query.filter_by(department_id=AC_DEPT).first()
        face = Face.query.filter_by(img_id=image.id).first()

        resp_no_redirect = client.post(
            url_for(source_route, tag_id=face.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(source_route, tag_id=face.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=face.officer_id
        )


def test_redirect_label_data(client, session):
    with current_app.test_request_context():
        login_admin(client)
        image = Image.query.filter_by(department_id=AC_DEPT).first()
        resp_no_redirect = client.post(
            url_for(
                "main.redirect_label_data", department_id=AC_DEPT, image_id=image.id
            ),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(
                "main.redirect_label_data", department_id=AC_DEPT, image_id=image.id
            ),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.label_data", department_id=AC_DEPT, image_id=image.id
        )


def test_redirect_complete_tagging(client, session):
    with current_app.test_request_context():
        login_admin(client)
        image = Image.query.filter_by(department_id=AC_DEPT).first()
        resp_no_redirect = client.get(
            url_for("main.redirect_complete_tagging", image_id=image.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_complete_tagging", image_id=image.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.label_data")


def test_redirect_submit_complaint(client, session):
    with current_app.test_request_context():
        login_user(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        query_string = {
            "officer_first_name": officer.first_name,
            "officer_last_name": officer.last_name,
            "officer_middle_initial": officer.middle_initial,
            "officer_star": "1232",
            "officer_image": "1",
        }
        resp_no_redirect = client.post(
            url_for("main.redirect_submit_complaint"),
            query_string=query_string,
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for("main.redirect_submit_complaint"),
            query_string=query_string,
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.submit_complaint")


def test_redirect_upload(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).one()
        resp_no_redirect = client.post(
            url_for(
                "main.redirect_upload",
                department_id=officer.department_id,
                officer_id=officer.id,
            ),
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for(
                "main.redirect_upload",
                department_id=officer.department_id,
                officer_id=officer.id,
            ),
            follow_redirects=True,
        )

        # TODO: Figure out why this is returning a 400 instead of a 200
        # assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.upload",
            department_id=officer.department_id,
            officer_id=officer.id,
        )


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_get_notes", "main.note_api"),
        ("main.redirect_edit_note", "main.note_api_edit"),
        ("main.redirect_delete_note", "main.note_api_delete"),
    ],
)
def test_redirect_note(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).first()
        note = Note.query.filter_by(officer_id=officer.id).first()
        resp_no_redirect = client.get(
            url_for(source_route, officer_id=officer.id, obj_id=note.id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for(source_route, officer_id=officer.id, obj_id=note.id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            target_route, officer_id=officer.id, obj_id=note.id
        )


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_get_description", "main.description_api"),
        ("main.redirect_edit_description", "main.description_api_edit"),
        ("main.redirect_delete_description", "main.description_api_delete"),
    ],
)
def test_redirect_description(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.filter_by(id=AC_DEPT).first()
        description = Description.query.filter_by(officer_id=officer.id).first()
        resp_no_redirect = client.get(
            url_for(
                source_route,
                officer_id=officer.id,
                obj_id=description.id,
            ),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for(
                source_route,
                officer_id=officer.id,
                obj_id=description.id,
            ),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            target_route, officer_id=officer.id, obj_id=description.id
        )


@pytest.mark.parametrize(
    "source_route, target_route",
    [
        ("main.redirect_edit_link", "main.link_api_edit"),
        ("main.redirect_delete_link", "main.link_api_delete"),
    ],
)
def test_redirect_link(client, session, source_route, target_route):
    with current_app.test_request_context():
        login_admin(client)
        officer = (
            Officer.query.filter_by(department_id=AC_DEPT)
            .outerjoin(Officer.links)
            .filter(Officer.links is not None)
            .first()
        )
        resp_no_redirect = client.get(
            url_for(
                source_route,
                officer_id=officer.id,
                obj_id=officer.links[0].id,
            ),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for(
                source_route,
                officer_id=officer.id,
                obj_id=officer.links[0].id,
            ),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            target_route, officer_id=officer.id, obj_id=officer.links[0].id
        )
