# Routing and view tests
from datetime import date, datetime, time
from http import HTTPStatus

import pytest
from flask import current_app, url_for
from sqlalchemy.orm import joinedload

from OpenOversight.app.main.forms import (
    IncidentForm,
    LicensePlateForm,
    LinkForm,
    LocationForm,
    OOIdForm,
)
from OpenOversight.app.models.database import Department, Incident, Officer, User
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.routes.route_helpers import (
    login_ac,
    login_admin,
    login_user,
    process_form_data,
)


@pytest.mark.parametrize(
    "route", ["/incidents/", "/incidents/1", "/incidents/?department_id=1"]
)
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "route", ["incidents/1/edit", "incidents/new", "incidents/1/delete"]
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


@pytest.mark.parametrize(
    "route", ["incidents/1/edit", "incidents/new", "incidents/1/delete"]
)
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "report_number",
    [
        # Ensure different report number formats are accepted
        "42",
        "My-Special-Case",
        "PPP Case 92",
    ],
)
def test_admins_can_create_basic_incidents(report_number, mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        test_date = datetime(2000, 5, 25, 1, 45)

        address_form = LocationForm(
            street_name="AAAAA",
            cross_street1="BBBBB",
            city="FFFFF",
            state="IA",
            zip_code="03435",
        )
        # These have to have a dropdown selected because if not, an empty Unicode
        # string is sent, which does not mach the '' selector.
        link_form = LinkForm(link_type="video")
        license_plates_form = LicensePlateForm(state="AZ")
        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number=report_number,
            description="Something happened",
            department="1",
            address=address_form.data,
            links=[link_form.data],
            license_plates=[license_plates_form.data],
            officers=[],
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_new"), data=data, follow_redirects=True
        )
        assert rv.status_code == HTTPStatus.OK
        assert "created" in rv.data.decode(ENCODING_UTF_8)

        inc = Incident.query.filter_by(date=test_date.date()).first()
        assert inc is not None


def test_admins_cannot_create_incident_with_invalid_report_number(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)
        test_date = datetime(2000, 5, 25, 1, 45)
        report_number = "Will Not Work! #45"

        address_form = LocationForm(
            street_name="AAAAA",
            cross_street1="BBBBB",
            city="FFFFF",
            state="IA",
            zip_code="03435",
        )
        # These have to have a dropdown selected because if not, an empty Unicode
        # string is sent, which does not mach the '' selector.
        link_form = LinkForm(link_type="video")
        license_plates_form = LicensePlateForm(state="AZ")
        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number=report_number,
            description="Something happened",
            department="1",
            address=address_form.data,
            links=[link_form.data],
            license_plates=[license_plates_form.data],
            officers=[],
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_new"), data=data, follow_redirects=True
        )

        assert rv.status_code == HTTPStatus.OK
        assert "Report cannot contain special characters" in rv.data.decode(
            ENCODING_UTF_8
        )


def test_admins_can_edit_incident_date_and_address(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()
        inc_id = inc.id
        test_date = date(2017, 6, 25)
        test_time = time(1, 45)
        street_name = "Newest St"
        address_form = LocationForm(
            street_name=street_name,
            cross_street1="Your St",
            city="Boston",
            state="NH",
            zip_code="03435",
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state).data
            for lp in inc.license_plates
        ]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(test_date),
            time_field=str(test_time),
            report_number=inc.report_number,
            description=inc.description,
            department="1",
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "successfully updated" in rv.data.decode(ENCODING_UTF_8)
        updated = Incident.query.get(inc_id)
        assert updated.date == test_date
        assert updated.time == test_time
        assert updated.address.street_name == street_name


def test_admins_can_edit_incident_links_and_licenses(mockdata, client, session, faker):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code,
        )
        old_links = inc.links
        old_links_forms = [
            LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links
        ]
        new_url = faker.url()
        link_form = LinkForm(url=new_url, link_type="video")
        old_license_plates = inc.license_plates
        new_number = "453893"
        license_plates_form = LicensePlateForm(number=new_number, state="IA")
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(inc.date),
            time_field=str(inc.time),
            report_number=inc.report_number,
            description=inc.description,
            department="1",
            address=address_form.data,
            links=old_links_forms + [link_form.data],
            license_plates=[license_plates_form.data],
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "successfully updated" in rv.data.decode(ENCODING_UTF_8)
        # old links are still there
        for link in old_links:
            assert link in inc.links
        assert new_url in [link.url for link in inc.links]
        # old license plates are gone
        assert old_license_plates not in inc.license_plates
        assert len(inc.license_plates) == 1
        assert new_number in [lp.number for lp in inc.license_plates]


def test_admins_cannot_make_ancient_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code,
            created_by=inc.created_by,
        )
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=date(1899, 12, 5),
            time_field=str(inc.time),
            report_number=inc.report_number,
            description=inc.description,
            department="1",
            address=address_form.data,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Incidents prior to 1900 not allowed." in rv.data.decode(ENCODING_UTF_8)


def test_admins_cannot_make_incidents_without_state(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        user = User.query.filter_by(is_administrator=True).first()
        test_date = datetime(2000, 5, 25, 1, 45)
        report_number = "42"

        address_form = LocationForm(
            street_name="AAAAA",
            cross_street1="BBBBB",
            city="FFFFF",
            state="",
            zip_code="03435",
            created_by=user.id,
        )
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in Officer.query.all()[:5]]

        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number=report_number,
            description="Something happened",
            department="1",
            address=address_form.data,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        incident_count_before = Incident.query.count()
        rv = client.post(
            url_for("main.incident_api_new"), data=data, follow_redirects=True
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Must select a state." in rv.data.decode(ENCODING_UTF_8)
        assert incident_count_before == Incident.query.count()


def test_admins_cannot_make_incidents_with_multiple_validation_errors(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_admin(client)
        user = User.query.filter_by(is_administrator=True).first()
        test_date = datetime(2000, 5, 25, 1, 45)
        report_number = "42"

        address_form = LocationForm(
            street_name="AAAAA",
            cross_street1="BBBBB",
            # no city given => 'This field is required.'
            city="",
            state="NY",
            # invalid ZIP code => 'Zip codes must have 5 digits.'
            zip_code="0343",
            created_by=user.id,
        )

        # license plate number given, but no state selected =>
        # 'Must also select a state.'
        license_plate_form = LicensePlateForm(number="ABCDE", state="")
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in Officer.query.all()[:5]]

        form = IncidentForm(
            # no date given => 'This field is required.'
            date_field="",
            time_field=str(test_date.time()),
            report_number=report_number,
            description="Something happened",
            # invalid department id => 'This field is required.'
            department="-1",
            address=address_form.data,
            license_plates=[license_plate_form.data],
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        incident_count_before = Incident.query.count()
        rv = client.post(
            url_for("main.incident_api_new"), data=data, follow_redirects=True
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Must also select a state." in rv.data.decode(ENCODING_UTF_8)
        assert "Zip codes must have 5 digits." in rv.data.decode(ENCODING_UTF_8)
        assert rv.data.decode(ENCODING_UTF_8).count("This field is required.") >= 3
        assert incident_count_before == Incident.query.count()


def test_admins_can_edit_incident_officers(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        user = User.query.filter_by(is_administrator=True).first()

        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code,
            created_by=inc.created_by,
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type, created_by=user.id).data
            for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state, created_by=user.id).data
            for lp in inc.license_plates
        ]

        old_officers = inc.officers
        old_officer_ids = [officer.id for officer in inc.officers]
        old_ooid_forms = [OOIdForm(oo_id=the_id) for the_id in old_officer_ids]
        # get a new officer that is different from the old officers
        new_officer = Officer.query.except_(
            Officer.query.filter(Officer.id.in_(old_officer_ids))
        ).first()
        new_ooid_form = OOIdForm(oo_id=new_officer.id)

        form = IncidentForm(
            date_field=str(inc.date),
            time_field=str(inc.time),
            report_number=inc.report_number,
            description=inc.description,
            department="1",
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=old_ooid_forms + [new_ooid_form],
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "successfully updated" in rv.data.decode(ENCODING_UTF_8)
        for officer in old_officers:
            assert officer in inc.officers
        assert new_officer.id in [off.id for off in inc.officers]


def test_admins_cannot_edit_non_existing_officers(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        user = User.query.filter_by(is_administrator=True).first()

        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code,
            created_by=inc.created_by,
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type, created_by=user.id).data
            for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state).data
            for lp in inc.license_plates
        ]

        old_officers = inc.officers
        old_officer_ids = [officer.id for officer in inc.officers]
        old_ooid_forms = [OOIdForm(oo_id=the_id) for the_id in old_officer_ids]
        # create an OOIdForm with an invalid officer ID
        new_ooid_form = OOIdForm(oo_id="99999999999999999")

        form = IncidentForm(
            date_field=str(inc.date),
            time_field=str(inc.time),
            report_number=inc.report_number,
            description=inc.description,
            department="1",
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=old_ooid_forms + [new_ooid_form],
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Not a valid officer id" in rv.data.decode(ENCODING_UTF_8)
        for officer in old_officers:
            assert officer in inc.officers


def test_ac_can_edit_incidents_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        user = User.query.filter_by(ac_department_id=AC_DEPT).first()

        inc = Incident.query.filter_by(department_id=AC_DEPT).first()
        test_date = datetime(2017, 6, 25, 1, 45)
        street_name = "Newest St"
        address_form = LocationForm(
            street_name=street_name,
            cross_street1="Your St",
            city="Boston",
            state="NH",
            zip_code="03435",
            created_by=user.id,
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type, created_by=user.id).data
            for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state, created_by=user.id).data
            for lp in inc.license_plates
        ]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department=AC_DEPT,
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "successfully updated" in rv.data.decode(ENCODING_UTF_8)
        assert inc.date == test_date.date()
        assert inc.time == test_date.time()
        assert inc.address.street_name == street_name


def test_ac_cannot_edit_incidents_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        user = User.query.filter_by(
            ac_department_id=None, is_administrator=False
        ).first()

        inc = Incident.query.except_(
            Incident.query.filter_by(department_id=AC_DEPT)
        ).first()
        test_date = datetime(2017, 6, 25, 1, 45)
        street_name = "Not Allowed St"
        address_form = LocationForm(
            street_name=street_name,
            cross_street1="Your St",
            city="Boston",
            state="NH",
            zip_code="03435",
            created_by=user.id,
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type, created_by=user.id).data
            for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state, created_by=user.id).data
            for lp in inc.license_plates
        ]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(test_date.date()),
            time_field=str(test_date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department=AC_DEPT,
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admins_can_delete_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        incident = Incident.query.first()
        inc_id = incident.id
        rv = client.post(
            url_for("main.incident_api_delete", obj_id=inc_id),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Incident.query.get(inc_id)
        assert deleted is None


def test_acs_can_delete_incidents_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.filter_by(department_id=AC_DEPT).first()
        inc_id = incident.id
        rv = client.post(
            url_for("main.incident_api_delete", obj_id=inc_id),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        deleted = Incident.query.get(inc_id)
        assert deleted is None


def test_acs_cannot_delete_incidents_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.except_(
            Incident.query.filter_by(department_id=AC_DEPT)
        ).first()
        inc_id = incident.id
        rv = client.post(
            url_for("main.incident_api_delete", obj_id=inc_id),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN
        not_deleted = Incident.query.get(inc_id)
        assert not_deleted.id is inc_id


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.filter_by(department_id=AC_DEPT).first()
        rv = client.get(
            url_for("main.incident_api_edit", obj_id=incident.id),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "Update" in rv.data.decode(ENCODING_UTF_8)


def test_acs_cannot_get_edit_form_for_their_non_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.except_(
            Incident.query.filter_by(department_id=AC_DEPT)
        ).first()
        rv = client.get(
            url_for("main.incident_api_edit", obj_id=incident.id),
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_users_can_view_incidents_by_department(mockdata, client, session):
    with current_app.test_request_context():
        department = Department.query.first()
        department_incidents = Incident.query.filter_by(department_id=department.id)
        non_department_incidents = Incident.query.except_(
            Incident.query.filter_by(department_id=department.id)
        )
        rv = client.get(url_for("main.incident_api", department_id=department.id))

        # Requires that report numbers in test data not include other report numbers
        # Tests for report numbers in table formatting, because testing for the raw
        # report number can get false positives due to html encoding
        for incident in department_incidents:
            assert f"<td>{incident.report_number}</td>" in rv.data.decode(
                ENCODING_UTF_8
            )
        for incident in non_department_incidents:
            assert f"<td>{incident.report_number}</td>" not in rv.data.decode(
                ENCODING_UTF_8
            )


def test_admins_can_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        rv = client.get(url_for("main.incident_api", obj_id=1))
        assert "Creator" in rv.data.decode(ENCODING_UTF_8)


def test_acs_cannot_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        rv = client.get(url_for("main.incident_api", obj_id=1))
        assert "Creator" not in rv.data.decode(ENCODING_UTF_8)


def test_users_cannot_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        rv = client.get(url_for("main.incident_api", obj_id=1))
        assert "Creator" not in rv.data.decode(ENCODING_UTF_8)


def test_form_with_officer_id_prepopulates(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer_id = "1234"
        rv = client.get(url_for("main.incident_api_new", officer_id=officer_id))
        assert officer_id in rv.data.decode(ENCODING_UTF_8)


def test_incident_markdown(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(url_for("main.incident_api"))
        html = rv.data.decode()
        assert "<h3>A thing happened</h3>" in html
        assert "<p><strong>Markup</strong> description</p>" in html


def test_admins_cannot_inject_unsafe_html(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        user = User.query.filter_by(is_administrator=True).first()

        inc = Incident.query.options(
            joinedload(Incident.links),
            joinedload(Incident.license_plates),
            joinedload(Incident.officers),
        ).first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code,
        )
        links_forms = [
            LinkForm(url=link.url, link_type=link.link_type, created_by=user.id).data
            for link in inc.links
        ]
        license_plates_forms = [
            LicensePlateForm(number=lp.number, state=lp.state, created_by=user.id).data
            for lp in inc.license_plates
        ]

        old_officer_ids = [officer.id for officer in inc.officers]
        ooid_forms = [OOIdForm(oo_id=the_id) for the_id in old_officer_ids]

        form = IncidentForm(
            date_field=str(inc.date),
            time_field=str(inc.time),
            report_number=inc.report_number,
            description="<script>alert();</script>",
            department="1",
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms,
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for("main.incident_api_edit", obj_id=inc.id),
            data=data,
            follow_redirects=True,
        )
        assert rv.status_code == HTTPStatus.OK
        assert "successfully updated" in rv.data.decode(ENCODING_UTF_8)
        assert "<script>" not in rv.data.decode()
        assert "&lt;script&gt;" in rv.data.decode()


@pytest.mark.parametrize(
    "params,included_report_nums,excluded_report_nums",
    [
        ({"department_id": "1"}, ["42"], ["38", "39"]),
        ({"occurred_before": "2017-12-12"}, ["38", "42"], ["39"]),
        (
            {"occurred_after": "2017-12-10", "occurred_before": "2019-01-01"},
            ["38"],
            ["39", "42"],
        ),
        ({"report_number": "38"}, ["38"], ["42", "39"]),  # Base case
        ({"report_number": "3"}, ["38", "39"], ["42"]),  # Test inclusive match
        ({"report_number": "38 "}, ["38"], ["42", "39"]),  # Test trim
    ],
)
def test_users_can_search_incidents(
    params, included_report_nums, excluded_report_nums, mockdata, client, session
):
    with current_app.test_request_context():
        rv = client.get(url_for("main.incident_api", **params))

        for report_num in included_report_nums:
            assert f"<td>{report_num}</td>" in rv.data.decode(ENCODING_UTF_8)

        for report_num in excluded_report_nums:
            assert f"<td>{report_num}</td>" not in rv.data.decode(ENCODING_UTF_8)
