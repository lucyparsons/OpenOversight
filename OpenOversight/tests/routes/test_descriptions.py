import pytest
from datetime import datetime
from flask import url_for, current_app
from OpenOversight.tests.conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac


from OpenOversight.app.main.forms import TextForm, EditTextForm
from OpenOversight.app.models import db, Officer, Description, User


@pytest.mark.parametrize("route", [
    ('officer/1/description/1/edit'),
    ('officer/1/description/new'),
    ('officer/1/description/1/delete')
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


@pytest.mark.parametrize("route", [
    ('officer/1/description/1/edit'),
    ('officer/1/description/new'),
    ('officer/1/description/1/delete')
])
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == 403


def test_admins_can_create_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = 'I can haz descriptionz'
        admin = User.query.filter_by(email='jen@example.org').first()
        form = TextForm(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=admin.id
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 200
        assert 'created' in rv.data.decode('utf-8')

        created_description = Description.query.filter_by(text_contents=text_contents).first()
        assert created_description is not None
        assert created_description.date_created is not None


def test_acs_can_create_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.first()
        description = 'A description'
        ac = User.query.filter_by(email='raq929@example.org').first()
        form = TextForm(
            text_contents=description,
            officer_id=officer.id,
            creator_id=ac.id
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 200
        assert 'created' in rv.data.decode('utf-8')

        created_description = Description.query.filter_by(text_contents=description).first()
        assert created_description is not None
        assert created_description.date_created is not None


def test_admins_can_edit_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        old_description = 'meow'
        new_description = 'I can haz editing descriptionz'
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            creator_id=1,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert description.text_contents == new_description
        assert description.date_updated > original_date


def test_ac_can_edit_their_descriptions_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_description = 'meow'
        new_description = 'I can haz editing descriptionz'
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert description.text_contents == new_description
        assert description.date_updated > original_date


def test_ac_can_edit_others_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_description = 'meow'
        new_description = 'I can haz editing descriptionz'
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            creator_id=ac.id - 1,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert description.text_contents == new_description
        assert description.date_updated > original_date


def test_ac_cannot_edit_descriptions_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        old_description = 'meow'
        new_description = 'I can haz editing descriptionz'
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_admins_can_delete_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        description = Description.query.first()
        description_id = description.id
        rv = client.post(
            url_for('main.description_api', officer_id=description.officer_id, obj_id=description_id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Description.query.get(description_id)
        assert deleted is None


def test_acs_can_delete_their_descriptions_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        description = Description(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        description_id = description.id
        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Description.query.get(description_id)
        assert deleted is None


def test_acs_cannot_delete_descriptions_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        description = Description(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        description_id = description.id
        rv = client.post(
            url_for('main.description_api', officer_id=officer.id, obj_id=description.id) + '/delete',
            follow_redirects=True
        )

        assert rv.status_code == 403
        not_deleted = Description.query.get(description_id)
        assert not_deleted is not None


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        description = Description(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.description_api', obj_id=description.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Update' in rv.data.decode('utf-8')


def test_acs_can_get_others_edit_form(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        description = Description(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id - 1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.description_api', obj_id=description.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Update' in rv.data.decode('utf-8')


def test_acs_cannot_get_edit_form_for_their_non_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        description = Description(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.description_api', obj_id=description.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_users_can_see_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.first()
        text_contents = 'You can see me'
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a description that exists
        assert description in officer.descriptions
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')


def test_admins_can_see_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = 'Kittens see everything'
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        assert description in officer.descriptions
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')


def test_acs_can_see_descriptions_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        text_contents = 'I can haz descriptionz'
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a description that exists
        assert description in officer.descriptions
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')


def test_acs_can_see_descriptions_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        text_contents = 'Hello it me'
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a description that exists
        assert description in officer.descriptions
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')
