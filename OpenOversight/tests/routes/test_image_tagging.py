# Routing and view tests
import os
from http import HTTPStatus

import pytest
from flask import current_app, url_for
from mock import MagicMock, patch

from OpenOversight.app.main import views
from OpenOversight.app.main.forms import FaceTag
from OpenOversight.app.models import Department, Face, Image, Officer
from OpenOversight.app.utils.constants import ENCODING_UTF_8

from ..conftest import AC_DEPT
from .route_helpers import login_ac, login_admin, login_user


PROJECT_ROOT = os.path.abspath(os.curdir)


@pytest.mark.parametrize(
    "route",
    [
        "/label",
        "/tutorial",
        "/tag/1",
    ],
)
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.OK


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize(
    "route",
    [
        "/leaderboard",
        "/sort/department/1",
        "/cop_face/department/1",
        "/image/1",
        "/image/tagged/1",
    ],
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


# POST-only routes
@pytest.mark.parametrize(
    "route",
    [
        "/officer/3/assignment/new",
        "/tag/delete/1",
        "/tag/set_featured/1",
        "/image/classify/1/1",
    ],
)
def test_route_post_only(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_logged_in_user_can_access_sort_form(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for("main.sort_images", department_id=1), follow_redirects=True
        )
        assert b"Do you see uniformed law enforcement officers in the photo" in rv.data


def test_user_can_view_submission(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for("main.display_submission", image_id=1), follow_redirects=True
        )
        assert b"Image ID" in rv.data


def test_user_can_view_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(url_for("main.display_tag", tag_id=1), follow_redirects=True)
        assert b"Tag" in rv.data

        # Check that tag frame position is specified
        for attribute in (b"data-top", b"data-left", b"data-width", b"data-height"):
            assert attribute in rv.data


def test_admin_can_delete_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(url_for("main.delete_tag", tag_id=1), follow_redirects=True)
        assert b"Deleted this tag" in rv.data


def test_ac_can_delete_tag_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = Face.query.filter(Face.officer.has(department_id=AC_DEPT)).first()
        tag_id = tag.id

        rv = client.post(
            url_for("main.delete_tag", tag_id=tag_id), follow_redirects=True
        )
        assert b"Deleted this tag" in rv.data

        # test tag was deleted from database
        deleted_tag = Face.query.filter_by(id=tag_id).first()
        assert deleted_tag is None


def test_ac_cannot_delete_tag_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = (
            Face.query.join(Face.officer, aliased=True)
            .except_(Face.query.filter(Face.officer.has(department_id=AC_DEPT)))
            .first()
        )

        tag_id = tag.id

        rv = client.post(
            url_for("main.delete_tag", tag_id=tag_id), follow_redirects=True
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN

        # test tag was not deleted from database
        deleted_tag = Face.query.filter_by(id=tag_id).first()
        assert deleted_tag is not None


@patch(
    "OpenOversight.app.utils.general.serve_image",
    MagicMock(return_value=PROJECT_ROOT + "/app/static/images/test_cop1.png"),
)
def test_user_can_add_tag(mockdata, client, session):
    with current_app.test_request_context():
        mock = MagicMock(return_value=Image.query.first())
        with patch("OpenOversight.app.main.views.crop_image", mock):
            officer = Officer.query.filter_by(department_id=1).first()
            image = Image.query.filter_by(department_id=1).first()
            login_user(client)
            form = FaceTag(
                officer_id=officer.id,
                image_id=image.id,
                dataX=34,
                dataY=32,
                dataWidth=3,
                dataHeight=33,
            )
            rv = client.post(
                url_for("main.label_data", image_id=image.id),
                data=form.data,
                follow_redirects=True,
            )
            views.crop_image.assert_called_once()
            assert b"Tag added to database" in rv.data


def test_user_cannot_add_tag_if_it_exists(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(
            officer_id=tag.officer_id,
            image_id=tag.original_image_id,
            dataX=34,
            dataY=32,
            dataWidth=3,
            dataHeight=33,
        )

        rv = client.post(
            url_for("main.label_data", image_id=tag.original_image_id),
            data=form.data,
            follow_redirects=True,
        )
        assert (
            b"Tag already exists between this officer and image! Tag not added."
            in rv.data
        )


def test_user_cannot_tag_nonexistent_officer(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(
            officer_id=999999999999999999,
            image_id=tag.img_id,
            dataX=34,
            dataY=32,
            dataWidth=3,
            dataHeight=33,
        )

        rv = client.post(
            url_for("main.label_data", image_id=tag.img_id),
            data=form.data,
            follow_redirects=True,
        )
        assert b"Invalid officer ID" in rv.data


def test_user_cannot_tag_officer_mismatched_with_department(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(
            officer_id=tag.officer_id,
            image_id=tag.original_image_id,
            dataX=34,
            dataY=32,
            dataWidth=3,
            dataHeight=33,
        )

        rv = client.post(
            url_for("main.label_data", department_id=2, image_id=tag.original_image_id),
            data=form.data,
            follow_redirects=True,
        )
        assert (
            b"The officer is not in Chicago Police Department. Are you sure that is the correct OpenOversight ID?"
            in rv.data
        )


def test_user_can_finish_tagging(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for("main.complete_tagging", image_id=4), follow_redirects=True
        )
        assert b"Marked image as completed." in rv.data


def test_user_can_view_leaderboard(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(url_for("main.leaderboard"), follow_redirects=True)
        assert b"Top Users by Number of Images Sorted" in rv.data


def test_user_is_redirected_to_correct_department_after_tagging(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_user(client)
        department_id = 2
        image = Image.query.filter_by(department_id=department_id, faces=None).first()
        rv = client.get(
            url_for(
                "main.complete_tagging", image_id=image.id, department_id=department_id
            ),
            follow_redirects=True,
        )
        department = Department.query.get(department_id)

        assert rv.status_code == HTTPStatus.OK
        assert department.name in rv.data.decode(ENCODING_UTF_8)


def test_admin_can_set_featured_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for("main.set_featured_tag", tag_id=1), follow_redirects=True
        )
        assert b"Successfully set this tag as featured" in rv.data


def test_ac_can_set_featured_tag_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = Face.query.filter(Face.officer.has(department_id=AC_DEPT)).first()
        tag_id = tag.id

        rv = client.post(
            url_for("main.set_featured_tag", tag_id=tag_id), follow_redirects=True
        )
        assert b"Successfully set this tag as featured" in rv.data

        featured_tag = (
            Face.query.filter(Face.officer_id == tag.officer_id)
            .filter(Face.featured == True)  # noqa: E712
            .one_or_none()
        )
        assert featured_tag is not None


def test_ac_cannot_set_featured_tag_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = (
            Face.query.join(Face.officer, aliased=True)
            .except_(Face.query.filter(Face.officer.has(department_id=AC_DEPT)))
            .first()
        )

        tag_id = tag.id

        rv = client.post(
            url_for("main.set_featured_tag", tag_id=tag_id), follow_redirects=True
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN

        featured_tag = (
            Face.query.filter(Face.officer_id == tag.officer_id)
            .filter(Face.featured == True)  # noqa: E712
            .one_or_none()
        )
        assert featured_tag is None


@patch(
    "OpenOversight.app.utils.general.serve_image",
    MagicMock(return_value=PROJECT_ROOT + "/app/static/images/test_cop1.png"),
)
def test_featured_tag_replaces_others(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        tag1 = Face.query.first()
        officer = Officer.query.filter_by(id=tag1.officer_id).one()

        # Add second tag for officer
        second_image = (
            Image.query.filter(Image.department_id == officer.department_id)
            .filter(Image.id != tag1.img_id)
            .first()
        )
        assert second_image is not None
        mock = MagicMock(return_value=second_image)
        with patch("OpenOversight.app.main.views.crop_image", mock):
            form = FaceTag(
                officer_id=officer.id,
                image_id=second_image.id,
                dataX=34,
                dataY=32,
                dataWidth=3,
                dataHeight=33,
            )
            rv = client.post(
                url_for("main.label_data", image_id=second_image.id),
                data=form.data,
                follow_redirects=True,
            )
            views.crop_image.assert_called_once()
            assert b"Tag added to database" in rv.data

        tag2 = (
            Face.query.filter(Face.officer_id == tag1.officer_id)
            .filter(Face.id != tag1.id)
            .one_or_none()
        )
        assert tag2 is not None

        # Set tag 1 as featured
        rv = client.post(
            url_for("main.set_featured_tag", tag_id=tag1.id), follow_redirects=True
        )
        assert b"Successfully set this tag as featured" in rv.data

        tag1 = Face.query.filter(Face.id == tag1.id).one()
        assert tag1.featured is True

        # Set tag 2 as featured
        rv = client.post(
            url_for("main.set_featured_tag", tag_id=tag2.id), follow_redirects=True
        )
        assert b"Successfully set this tag as featured" in rv.data

        tag1 = Face.query.filter(Face.id == tag1.id).one()
        tag2 = Face.query.filter(Face.id == tag2.id).one()
        assert tag1.featured is False
        assert tag2.featured is True
