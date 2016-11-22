# Routing and view tests
import pytest
from flask import url_for, current_app
from OpenOversight.app.main.forms import FindOfficerForm, FindOfficerIDForm
from urlparse import urlparse


@pytest.mark.parametrize("route", [
    ('/'),
    ('/index'),
    ('/find'),
    ('/about'),
    ('/contact'),
    ('/privacy'),
    ('/label')
])
def test_routes_ok(route, client):
    rv = client.get(route)
    assert rv.status_code == 200


@pytest.mark.parametrize("route", [
    ('/gallery'),
    ('/upload'),
    ('/tagger_gallery')
])
def test_route_method_not_allowd(route, client):
    rv = client.get(route)
    assert rv.status_code == 405

#
# def test_find_form_submission(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/gallery'
#
#
# def test_bad_form(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm(dept='')
#         assert form.validate() == False
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/find'
#
#
# def test_find_form_redirect_submission(client, session):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 200


def test_tagger_lookup(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() == True
        rv = client.post(url_for('main.label_data'), data=form.data, follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_gallery'


def test_tagger_gallery(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() == True
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data)
        assert rv.status_code == 200


def test_tagger_gallery_bad_form(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(dept='')
        assert form.validate() == False
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data, follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/label'
