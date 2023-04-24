from datetime import datetime
from http import HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.main.forms import EditTextForm, TextForm
from OpenOversight.app.models import Note, Officer, User, db
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.conftest import AC_DEPT

from .route_helpers import login_ac, login_admin, login_user


@pytest.mark.parametrize(
    "route",
    ["officer/1/note/1/edit", "officer/1/note/new", "officer/1/note/1/delete"],
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


@pytest.mark.parametrize(
    "route",
    ["officer/1/note/1/edit", "officer/1/note/new", "officer/1/note/1/delete"],
)
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_officer_notes_markdown(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)  # need to be admin or AC to see notes
        rv = client.get(url_for("main.officer_profile", officer_id=1))
        assert rv.status_code == HTTPStatus.OK
        html = rv.data.decode()
        assert "<h3>A markdown note</h3>" in html
        assert "<p>A <strong>test</strong> note!</p>" in html


def test_admins_cannot_inject_unsafe_html(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = "New note\n<script>alert();</script>"
        admin = User.query.filter_by(email="jen@example.org").first()
        form = TextForm(
            text_contents=text_contents, officer_id=officer.id, creator_id=admin.id
        )

        rv = client.post(
            url_for("main.note_api", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)
        assert "<script>" not in rv.data.decode()
        assert "&lt;script&gt;" in rv.data.decode()


def test_admins_can_create_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = "I can haz notez"
        admin = User.query.filter_by(email="jen@example.org").first()
        form = TextForm(
            text_contents=text_contents, officer_id=officer.id, creator_id=admin.id
        )

        rv = client.post(
            url_for("main.note_api", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)

        created_note = Note.query.filter_by(text_contents=text_contents).first()
        assert created_note is not None
        assert created_note.date_created is not None


def test_acs_can_create_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.first()
        note = "I can haz notez"
        ac = User.query.filter_by(email="raq929@example.org").first()
        form = TextForm(text_contents=note, officer_id=officer.id, creator_id=ac.id)

        rv = client.post(
            url_for("main.note_api", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)

        created_note = Note.query.filter_by(text_contents=note).first()
        assert created_note is not None
        assert created_note.date_created is not None


def test_admins_can_edit_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        old_note = "meow"
        new_note = "I can haz editing notez"
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
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/edit",
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_can_edit_their_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email="raq929@example.org").first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_note = "meow"
        new_note = "I can haz editing notez"
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
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/edit",
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_can_edit_others_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email="raq929@example.org").first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_note = "meow"
        new_note = "I can haz editing notez"
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
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/edit",
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert note.text_contents == new_note
        assert note.date_updated > original_date


def test_ac_cannot_edit_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        ac = User.query.filter_by(email="raq929@example.org").first()
        old_note = "meow"
        new_note = "I can haz editing notez"
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
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/edit",
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admins_can_delete_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        note = Note.query.first()
        note_id = note.id
        rv = client.post(
            url_for("main.note_api", officer_id=note.officer_id, obj_id=note_id)
            + "/delete",
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Note.query.get(note_id)
        assert deleted is None


def test_acs_can_delete_their_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        ac = User.query.filter_by(email="raq929@example.org").first()
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        note = Note(
            text_contents="Hello",
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        note_id = note.id
        rv = client.post(
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/delete",
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Note.query.get(note_id)
        assert deleted is None


def test_acs_cannot_delete_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        note = Note(
            text_contents="Hello",
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        note_id = note.id
        rv = client.post(
            url_for("main.note_api", officer_id=officer.id, obj_id=note.id) + "/delete",
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN
        not_deleted = Note.query.get(note_id)
        assert not_deleted is not None


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email="raq929@example.org").first()
        note = Note(
            text_contents="Hello",
            officer_id=officer.id,
            creator_id=ac.id,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for("main.note_api", obj_id=note.id, officer_id=officer.id) + "/edit",
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Update" in rv.data.decode(ENCODING_UTF_8)


def test_acs_can_get_others_edit_form(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        ac = User.query.filter_by(email="raq929@example.org").first()
        note = Note(
            text_contents="Hello",
            officer_id=officer.id,
            creator_id=ac.id - 1,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for("main.note_api", obj_id=note.id, officer_id=officer.id) + "/edit",
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Update" in rv.data.decode(ENCODING_UTF_8)


def test_acs_cannot_get_edit_form_for_their_non_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        note = Note(
            text_contents="Hello",
            officer_id=officer.id,
            creator_id=2,
            date_created=datetime.now(),
            date_updated=datetime.now(),
        )
        db.session.add(note)
        db.session.commit()
        rv = client.get(
            url_for("main.note_api", obj_id=note.id, officer_id=officer.id) + "/edit",
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_users_cannot_see_notes(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.first()
        text_contents = "U can't see meeee"
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
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == HTTPStatus.OK
        assert text_contents not in rv.data.decode(ENCODING_UTF_8)


def test_admins_can_see_notes(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = "Kittens see everything"
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
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert note in officer.notes
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in rv.data.decode(ENCODING_UTF_8)


def test_acs_can_see_notes_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        text_contents = "I can haz notez"
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
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in rv.data.decode(ENCODING_UTF_8)


def test_acs_cannot_see_notes_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        text_contents = "Hello it me"
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
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a note that exists
        assert note in officer.notes
        assert rv.status_code == HTTPStatus.OK
        assert text_contents not in rv.data.decode(ENCODING_UTF_8)
