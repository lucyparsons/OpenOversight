import pytest
from datetime import datetime
from flask import url_for, current_app
from OpenOversight.tests.conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac


from OpenOversight.app.main.forms import TextForm, EditTextForm
from OpenOversight.app.models import db, Officer, Note, User


@pytest.mark.parametrize("route", [
    ('officer/1/note/1/edit'),
    ('officer/1/note/new'),
    ('officer/1/note/1/delete')
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


@pytest.mark.parametrize("route", [
    ('officer/1/note/1/edit'),
    ('officer/1/note/new'),
    ('officer/1/note/1/delete')
])
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == 403


def test_admins_can_create_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = 'I can haz notez'
        admin = User.query.filter_by(email='jen@example.org').first()
        form = TextForm(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=admin.id
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 200
        assert 'created' in rv.data.decode('utf-8')

        created_note = Note.query.filter_by(text_contents=text_contents).first()
        assert created_note is not None
        assert created_note.date_created is not None


def test_acs_can_create_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.first()
        note = 'I can haz notez'
        ac = User.query.filter_by(email='raq929@example.org').first()
        form = TextForm(
            text_contents=note,
            officer_id=officer.id,
            creator_id=ac.id
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 200
        assert 'created' in rv.data.decode('utf-8')

        created_note = Note.query.filter_by(text_contents=note).first()
        assert created_note is not None
        assert created_note.date_created is not None


def test_admins_can_edit_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        old_note = 'meow'
        new_note = 'I can haz editing notez'
        original_date = datetime.now()
        note = Note(
            text_contents=old_note,
            officer_id=officer.id,
            creator_id=1,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(note)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_note,
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_can_edit_their_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_note = 'meow'
        new_note = 'I can haz editing notez'
        original_date = datetime.now()
        note = Note(
            text_contents=old_note,
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(note)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_note,
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_can_edit_others_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_note = 'meow'
        new_note = 'I can haz editing notez'
        original_date = datetime.now()
        note = Note(
            text_contents=old_note,
            officer_id=officer.id,
            creator_id=ac.id - 1,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(note)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_note,
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'updated' in rv.data.decode('utf-8')

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_cannot_edit_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        old_note = 'meow'
        new_note = 'I can haz editing notez'
        original_date = datetime.now()
        note = Note(
            text_contents=old_note,
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=original_date,
            date_updated=original_date,
        )
        db.session.add(note)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_note,
        )

        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/edit',
            data=form.data,
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_admins_can_delete_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        note = Note.query.first()
        note_id = note.id
        rv = client.post(
            url_for('main.note_api', officer_id=note.officer_id, obj_id=note_id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Note.query.get(note_id)
        assert deleted is None


def test_acs_can_delete_their_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email='raq929@example.org').first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        note = Note(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        note_id = note.id
        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Note.query.get(note_id)
        assert deleted is None


def test_acs_cannot_delete_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        note = Note(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        note_id = note.id
        rv = client.post(
            url_for('main.note_api', officer_id=officer.id, obj_id=note.id) + '/delete',
            follow_redirects=True
        )

        assert rv.status_code == 403
        not_deleted = Note.query.get(note_id)
        assert not_deleted is not None


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        note = Note(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.note_api', obj_id=note.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Update' in rv.data.decode('utf-8')


def test_acs_can_get_others_edit_form(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email='raq929@example.org').first()
        note = Note(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=ac.id - 1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.note_api', obj_id=note.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Update' in rv.data.decode('utf-8')


def test_acs_cannot_get_edit_form_for_their_non_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        note = Note(
            text_contents='Hello',
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.note_api', obj_id=note.id, officer_id=officer.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_users_cannot_see_notes(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.first()
        text_contents = 'U can\'t see meeee'
        note = Note(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == 200
        assert text_contents not in rv.data.decode('utf-8')


def test_admins_can_see_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = 'Kittens see everything'
        note = Note(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        assert note in officer.notes
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')


def test_acs_can_see_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        text_contents = 'I can haz notez'
        note = Note(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == 200
        assert text_contents in rv.data.decode('utf-8')


def test_acs_cannot_see_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        text_contents = 'Hello it me'
        note = Note(
            text_contents=text_contents,
            officer_id=officer.id,
            creator_id=1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == 200
        assert text_contents not in rv.data.decode('utf-8')
