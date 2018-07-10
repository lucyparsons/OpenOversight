# Routing and view tests
import pytest
from mock import MagicMock, patch
from flask import url_for, current_app
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from ..conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac
from OpenOversight.app.main import views

from OpenOversight.app.main.forms import FaceTag, FindOfficerIDForm
from OpenOversight.app.models import Face, Image, Department


@pytest.mark.parametrize("route", [
    ('/tagger_find'),
    ('/label'),
    ('/tutorial'),
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route", [
    ('/leaderboard'),
    ('/sort/department/1'),
    ('/cop_face/department/1'),
    ('/image/1'),
    ('/image/tagged/1'),
    ('/tag/1'),
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


# POST-only routes
@pytest.mark.parametrize("route", [
    ('/officer/3/assignment/new'),
    ('/tag/delete/1'),
    ('/image/classify/1/1')
])
def test_route_post_only(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 405


def test_tagger_lookup(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(dept='')
        assert form.validate() is True
        rv = client.post(url_for('main.get_ooid'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_gallery'


def test_tagger_gallery(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(dept='')
        assert form.validate() is True
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data)
        assert rv.status_code == 200


def test_tagger_gallery_bad_form(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(badge='THIS IS NOT VALID')
        assert form.validate() is False
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_find'


def test_logged_in_user_can_access_sort_form(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.sort_images', department_id=1),
            follow_redirects=True
        )
        assert b'Do you see uniformed law enforcement officers in the photo' in rv.data


def test_user_can_view_submission(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.display_submission', image_id=1),
            follow_redirects=True
        )
        assert b'Image ID' in rv.data


def test_user_can_view_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.display_tag', tag_id=1),
            follow_redirects=True
        )
        assert b'Tag' in rv.data


def test_admin_can_delete_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for('main.delete_tag', tag_id=1),
            follow_redirects=True
        )
        assert b'Deleted this tag' in rv.data


def test_ac_can_delete_tag_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = Face.query.filter(Face.officer.has(department_id=AC_DEPT)).first()
        tag_id = tag.id

        rv = client.post(
            url_for('main.delete_tag', tag_id=tag_id),
            follow_redirects=True
        )
        assert b'Deleted this tag' in rv.data

        # test tag was deleted from database
        deleted_tag = Face.query.filter_by(id=tag_id).first()
        assert deleted_tag is None


def test_ac_cannot_delete_tag_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        tag = Face.query.join(Face.officer, aliased=True).except_(Face.query.filter(Face.officer.has(department_id=AC_DEPT))).first()

        tag_id = tag.id

        rv = client.post(
            url_for('main.delete_tag', tag_id=tag_id),
            follow_redirects=True
        )
        assert rv.status_code == 403

        # test tag was not deleted from database
        deleted_tag = Face.query.filter_by(id=tag_id).first()
        assert deleted_tag is not None


def test_user_can_add_tag(mockdata, client, session, monkeypatch):
    with current_app.test_request_context():
        mock = MagicMock(return_value=Image.query.first())
        with patch('OpenOversight.app.main.views.get_uploaded_image', mock):
            login_user(client)
            officer = Image.query.filter_by(department_id=1).first()
            image = Image.query.filter_by(department_id=1).first()
            form = FaceTag(officer_id=officer.id,
                           image_id=image.id,
                           dataX=34,
                           dataY=32,
                           dataWidth=3,
                           dataHeight=33)

            rv = client.post(
                url_for('main.label_data', image_id=image.id),
                data=form.data,
                follow_redirects=True
            )
            views.get_uploaded_image.assert_called_once()
            assert 'Tag added to database' in rv.data


def test_user_cannot_add_tag_if_it_exists(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(officer_id=tag.officer_id,
                       image_id=tag.img_id,
                       dataX=34,
                       dataY=32,
                       dataWidth=3,
                       dataHeight=33)

        rv = client.post(
            url_for('main.label_data', image_id=tag.img_id),
            data=form.data,
            follow_redirects=True
        )
        assert b'Tag already exists between this officer and image! Tag not added.' in rv.data


def test_user_cannot_tag_nonexistent_officer(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(officer_id=999999999999999999,
                       image_id=tag.img_id,
                       dataX=34,
                       dataY=32,
                       dataWidth=3,
                       dataHeight=33)

        rv = client.post(
            url_for('main.label_data', image_id=tag.img_id),
            data=form.data,
            follow_redirects=True
        )
        assert b'Invalid officer ID' in rv.data


def test_user_can_finish_tagging(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.complete_tagging', image_id=4),
            follow_redirects=True
        )
        assert b'Marked image as completed.' in rv.data


def test_user_can_view_leaderboard(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.leaderboard'),
            follow_redirects=True
        )
        assert b'Top Users by Number of Images Sorted' in rv.data


def test_user_is_redirected_to_correct_department_after_tagging(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        department_id = 2
        image = Image.query.filter_by(department_id=department_id, faces=None).first()
        rv = client.get(
            url_for('main.complete_tagging', image_id=image.id, department_id=department_id),
            follow_redirects=True
        )
        department = Department.query.get(department_id)

        assert rv.status_code == 200
        assert department.name in rv.data.decode('utf-8')
