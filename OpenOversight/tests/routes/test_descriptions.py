from datetime import datetime
from http import HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.main.forms import EditTextForm, TextForm
from OpenOversight.app.models.database import Description, Officer, User, db
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.constants import ADMIN_USER_EMAIL
from OpenOversight.tests.routes.route_helpers import login_ac, login_admin, login_user


@pytest.mark.parametrize(
    "route",
    [
        "officers/1/descriptions/1/edit",
        "officers/1/descriptions/new",
        "officers/1/descriptions/1/delete",
    ],
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


@pytest.mark.parametrize(
    "route",
    [
        "officers/1/descriptions/1/edit",
        "officers/1/descriptions/new",
        "officers/1/descriptions/1/delete",
    ],
)
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_officer_descriptions_markdown(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(url_for("main.officer_profile", officer_id=1))
        assert rv.status_code == HTTPStatus.OK
        html = rv.data.decode()
        assert "<h3>A markdown description</h3>" in html
        assert "<p>A <strong>test</strong> description!</p>" in html


def test_admins_cannot_inject_unsafe_html(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = "New description\n<script>alert();</script>"
        form = TextForm(text_contents=text_contents, officer_id=officer.id)

        rv = client.post(
            url_for("main.description_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)
        assert "<script>" not in rv.data.decode()
        assert "&lt;script&gt;" in rv.data.decode()


def test_admins_can_create_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        _, admin = login_admin(client)
        officer = Officer.query.first()
        text_contents = "I can haz descriptionz"
        form = TextForm(text_contents=text_contents, officer_id=officer.id)

        rv = client.post(
            url_for("main.description_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)

        created_description = Description.query.filter_by(
            text_contents=text_contents
        ).first()
        assert created_description is not None
        assert created_description.created_at is not None
        assert created_description.created_by == admin.id
        assert created_description.last_updated_by == admin.id


def test_acs_can_create_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        _, ac = login_ac(client)
        officer = Officer.query.first()
        description = "A description"
        form = TextForm(text_contents=description, officer_id=officer.id)

        rv = client.post(
            url_for("main.description_api_new", officer_id=officer.id),
            data=form.data,
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)

        created_description = Description.query.filter_by(
            text_contents=description
        ).first()
        assert created_description is not None
        assert created_description.created_at is not None
        assert created_description.created_by == ac.id
        assert created_description.last_updated_by == ac.id


def test_admins_can_edit_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        _, admin = login_admin(client)
        officer = Officer.query.first()
        old_description = "meow"
        new_description = "I can haz editing descriptionz"
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            created_at=original_date,
            last_updated_at=original_date,
            created_by=admin.id,
            last_updated_by=admin.id,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for(
                "main.description_api_edit",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert description.text_contents == new_description
        assert description.created_at == original_date
        assert description.last_updated_at > original_date
        assert description.created_by == admin.id
        assert description.last_updated_by == admin.id


def test_ac_can_edit_their_descriptions_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_description = "meow"
        new_description = "I can haz editing descriptionz"
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            created_at=original_date,
            last_updated_at=original_date,
            created_by=user.id,
            last_updated_by=user.id,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for(
                "main.description_api_edit",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert description.text_contents == new_description
        assert description.created_at == original_date
        assert description.last_updated_at > original_date
        assert description.created_by == user.id
        assert description.last_updated_by == user.id


def test_ac_can_edit_others_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        old_description = "meow"
        new_description = "I can haz editing descriptionz"
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            created_at=original_date,
            last_updated_at=original_date,
            created_by=user.id - 1,
            last_updated_by=user.id,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for(
                "main.description_api_edit",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "updated" in rv.data.decode(ENCODING_UTF_8)

        assert description.text_contents == new_description
        assert description.last_updated_at > original_date
        assert description.created_by == user.id - 1
        assert description.last_updated_by == user.id


def test_ac_cannot_edit_descriptions_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()

        old_description = "meow"
        new_description = "I can haz editing descriptionz"
        original_date = datetime.now()
        description = Description(
            text_contents=old_description,
            officer_id=officer.id,
            created_at=original_date,
            last_updated_at=original_date,
        )
        db.session.add(description)
        db.session.commit()

        form = EditTextForm(
            text_contents=new_description,
        )

        rv = client.post(
            url_for(
                "main.description_api_edit",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            data=form.data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admins_can_delete_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        description = Description.query.first()
        description_id = description.id
        rv = client.post(
            url_for(
                "main.description_api_delete",
                officer_id=description.officer_id,
                obj_id=description_id,
            ),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Description.query.get(description_id)
        assert deleted is None


def test_acs_can_delete_their_descriptions_in_their_department(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        now = datetime.now()
        description = Description(
            text_contents="Hello",
            officer_id=officer.id,
            created_at=now,
            last_updated_at=now,
        )
        db.session.add(description)
        db.session.commit()
        description_id = description.id
        rv = client.post(
            url_for(
                "main.description_api_delete",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Description.query.get(description_id)
        assert deleted is None


def test_acs_cannot_delete_descriptions_not_in_their_department(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        now = datetime.now()
        description = Description(
            text_contents="Hello",
            officer_id=officer.id,
            created_at=now,
            last_updated_at=now,
        )
        db.session.add(description)
        db.session.commit()
        description_id = description.id
        rv = client.post(
            url_for(
                "main.description_api_delete",
                officer_id=officer.id,
                obj_id=description.id,
            ),
            follow_redirects=True,
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN
        not_deleted = Description.query.get(description_id)
        assert not_deleted is not None


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        description = Description(
            text_contents="Hello",
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for(
                "main.description_api_edit",
                obj_id=description.id,
                officer_id=officer.id,
            ),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Update" in rv.data.decode(ENCODING_UTF_8)


def test_acs_can_get_others_edit_form(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        description = Description(
            text_contents="Hello",
            officer_id=officer.id,
            created_by=user.id - 1,
            last_updated_by=user.id - 1,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for(
                "main.description_api_edit",
                obj_id=description.id,
                officer_id=officer.id,
            ),
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
        description = Description(
            text_contents="Hello",
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for(
                "main.description_api_edit",
                obj_id=description.id,
                officer_id=officer.id,
            ),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_users_can_see_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        admin = User.query.filter_by(email=ADMIN_USER_EMAIL).first()
        officer = Officer.query.first()
        text_contents = "You can see me"
        description = Description(
            created_by=admin.id,
            text_contents=text_contents,
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a description that exists
        assert description in officer.descriptions
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in rv.data.decode(ENCODING_UTF_8)


def test_admins_can_see_descriptions(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer = Officer.query.first()
        text_contents = "Kittens see everything"
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert description in officer.descriptions
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in rv.data.decode(ENCODING_UTF_8)


def test_acs_can_see_descriptions_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        text_contents = "I can haz descriptionz"
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a description that exists
        assert description in officer.descriptions
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in rv.data.decode(ENCODING_UTF_8)


def test_acs_can_see_descriptions_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.except_(
            Officer.query.filter_by(department_id=AC_DEPT)
        ).first()
        _, user = login_ac(client)
        text_contents = "Hello it me"
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
        )
        db.session.add(description)
        db.session.commit()
        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        # ensures we're looking for a description that exists
        response_text = rv.data.decode(ENCODING_UTF_8)
        assert description in officer.descriptions
        assert rv.status_code == HTTPStatus.OK
        assert text_contents in response_text
        assert user.username in response_text


def test_anonymous_users_cannot_see_description_creators(mockdata, client, session):
    with current_app.test_request_context():
        officer = Officer.query.first()
        ac = User.query.filter_by(ac_department_id=AC_DEPT).first()
        text_contents = "All we have is each other"
        description = Description(
            text_contents=text_contents,
            officer_id=officer.id,
            created_by=ac.id,
            last_updated_by=ac.id,
        )
        db.session.add(description)
        db.session.commit()

        rv = client.get(
            url_for("main.officer_profile", officer_id=officer.id),
            follow_redirects=True,
        )
        assert description in officer.descriptions
        assert rv.status_code == HTTPStatus.OK
        assert ac.username not in rv.data.decode(ENCODING_UTF_8)
