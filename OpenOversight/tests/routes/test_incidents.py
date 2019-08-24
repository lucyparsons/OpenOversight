# Routing and view tests
import pytest
from datetime import datetime, date
from flask import url_for, current_app
from OpenOversight.tests.conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac, process_form_data


from OpenOversight.app.main.forms import IncidentForm, LocationForm, LinkForm, LicensePlateForm, OOIdForm
from OpenOversight.app.models import Incident, Officer, Department


@pytest.mark.parametrize("route", [
    ('/incidents/'),
    ('/incidents/1'),
    ('/incidents/?department_id=1')
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


@pytest.mark.parametrize("route", [
    ('incidents/1/edit'),
    ('incidents/new'),
    ('incidents/1/delete')
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


@pytest.mark.parametrize("route", [
    ('incidents/1/edit'),
    ('incidents/new'),
    ('incidents/1/delete')
])
def test_route_admin_or_required(route, client, mockdata):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get(route)
        assert rv.status_code == 403


def test_admins_can_create_basic_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        date = datetime(2000, 5, 25, 1, 45)
        report_number = '42'

        address_form = LocationForm(
            street_name='AAAAA',
            cross_street1='BBBBB',
            city='FFFFF',
            state='IA',
            zip_code='03435'
        )
        # These have to have a dropdown selected because if not, an empty Unicode string is sent, which does not mach the '' selector.
        link_form = LinkForm(link_type='video')
        license_plates_form = LicensePlateForm(state='AZ')
        form = IncidentForm(
            date_field=str(date.date()),
            time_field=str(date.time()),
            report_number=report_number,
            description='Something happened',
            department='1',
            address=address_form.data,
            links=[link_form.data],
            license_plates=[license_plates_form.data],
            officers=[]

        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api') + 'new',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'created' in rv.data.decode('utf-8')

        inc = Incident.query.filter_by(date=date).first()
        assert inc is not None


def test_admins_can_edit_incident_date_and_address(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.first()
        inc_id = inc.id
        new_date = datetime(2017, 6, 25, 1, 45)
        street_name = 'Newest St'
        address_form = LocationForm(
            street_name=street_name,
            cross_street1='Your St',
            city='Boston',
            state='NH',
            zip_code='03435'
        )
        links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        license_plates_forms = [LicensePlateForm(number=lp.number, state=lp.state).data for lp in inc.license_plates]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(new_date.date()),
            time_field=str(new_date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department='1',
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'successfully updated' in rv.data.decode('utf-8')
        updated = Incident.query.get(inc_id)
        assert updated.date == new_date
        assert updated.address.street_name == street_name


def test_admins_can_edit_incident_links_and_licenses(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code
        )
        old_links = inc.links
        old_links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        new_url = 'http://rachel.com'
        link_form = LinkForm(url='http://rachel.com', link_type='video')
        old_license_plates = inc.license_plates
        new_number = '453893'
        license_plates_form = LicensePlateForm(number=new_number, state='IA')
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(inc.date.date()),
            time_field=str(inc.date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department='1',
            address=address_form.data,
            links=old_links_forms + [link_form.data],
            license_plates=[license_plates_form.data],
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'successfully updated' in rv.data.decode('utf-8')
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
        inc = Incident.query.first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code
        )
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=date(1899, 12, 5),
            time_field=str(inc.date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department='1',
            address=address_form.data,
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Incidents prior to 1900 not allowed.' in rv.data.decode('utf-8')


def test_admins_cannot_make_incidents_without_state(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        date = datetime(2000, 5, 25, 1, 45)
        report_number = '42'

        address_form = LocationForm(
            street_name='AAAAA',
            cross_street1='BBBBB',
            city='FFFFF',
            state='',
            zip_code='03435'
        )
        ooid_forms = [OOIdForm(ooid=officer.id)
                      for officer in Officer.query.all()[:5]]

        form = IncidentForm(
            date_field=str(date.date()),
            time_field=str(date.time()),
            report_number=report_number,
            description='Something happened',
            department='1',
            address=address_form.data,
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        incident_count_before = Incident.query.count()
        rv = client.post(
            url_for('main.incident_api') + 'new',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Must select a state.' in rv.data.decode('utf-8')
        assert incident_count_before == Incident.query.count()


def test_admins_cannot_make_incidents_with_multiple_validation_errors(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        date = datetime(2000, 5, 25, 1, 45)
        report_number = '42'

        address_form = LocationForm(
            street_name='AAAAA',
            cross_street1='BBBBB',
            # no city given => 'This field is required.'
            city='',
            state='NY',
            # invalid ZIP code => 'Zip codes must have 5 digits.'
            zip_code='0343'
        )

        # license plate number given, but no state selected => 'Must also select a state.'
        license_plate_form = LicensePlateForm(number='ABCDE', state='')
        ooid_forms = [OOIdForm(ooid=officer.id)
                      for officer in Officer.query.all()[:5]]

        form = IncidentForm(
            # no date given => 'This field is required.'
            date_field='',
            time_field=str(date.time()),
            report_number=report_number,
            description='Something happened',
            # invalid department id => 'This field is required.'
            department='-1',
            address=address_form.data,
            license_plates=[license_plate_form.data],
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        incident_count_before = Incident.query.count()
        rv = client.post(
            url_for('main.incident_api') + 'new',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Must also select a state.' in rv.data.decode('utf-8')
        assert 'Zip codes must have 5 digits.' in rv.data.decode('utf-8')
        assert rv.data.decode('utf-8').count('This field is required.') >= 3
        assert incident_count_before == Incident.query.count()


def test_admins_can_edit_incident_officers(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code
        )
        links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        license_plates_forms = [LicensePlateForm(number=lp.number, state=lp.state).data for lp in inc.license_plates]

        old_officers = inc.officers
        old_officer_ids = [officer.id for officer in inc.officers]
        old_ooid_forms = [OOIdForm(oo_id=the_id) for the_id in old_officer_ids]
        # get a new officer that is different from the old officers
        new_officer = Officer.query.except_(Officer.query.filter(Officer.id.in_(old_officer_ids))).first()
        new_ooid_form = OOIdForm(oo_id=new_officer.id)

        form = IncidentForm(
            date_field=str(inc.date.date()),
            time_field=str(inc.date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department='1',
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=old_ooid_forms + [new_ooid_form]
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'successfully updated' in rv.data.decode('utf-8')
        for officer in old_officers:
            assert officer in inc.officers
        assert new_officer.id in [off.id for off in inc.officers]


def test_admins_cannot_edit_nonexisting_officers(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        inc = Incident.query.first()

        address_form = LocationForm(
            street_name=inc.address.street_name,
            cross_street1=inc.address.cross_street1,
            cross_street2=inc.address.cross_street2,
            city=inc.address.city,
            state=inc.address.state,
            zip_code=inc.address.zip_code
        )
        links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        license_plates_forms = [LicensePlateForm(number=lp.number, state=lp.state).data for lp in inc.license_plates]

        old_officers = inc.officers
        old_officer_ids = [officer.id for officer in inc.officers]
        old_ooid_forms = [OOIdForm(oo_id=the_id) for the_id in old_officer_ids]
        # create an OOIdForm with an invalid officer ID
        new_ooid_form = OOIdForm(oo_id="99999999999999999")

        form = IncidentForm(
            date_field=str(inc.date.date()),
            time_field=str(inc.date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department='1',
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=old_ooid_forms + [new_ooid_form]
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Not a valid officer id' in rv.data.decode('utf-8')
        for officer in old_officers:
            assert officer in inc.officers


def test_ac_can_edit_incidents_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        inc = Incident.query.filter_by(department_id=AC_DEPT).first()
        new_date = datetime(2017, 6, 25, 1, 45)
        street_name = 'Newest St'
        address_form = LocationForm(
            street_name=street_name,
            cross_street1='Your St',
            city='Boston',
            state='NH',
            zip_code='03435'
        )
        links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        license_plates_forms = [LicensePlateForm(number=lp.number, state=lp.state).data for lp in inc.license_plates]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(new_date.date()),
            time_field=str(new_date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department=AC_DEPT,
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'successfully updated' in rv.data.decode('utf-8')
        assert inc.date == new_date
        assert inc.address.street_name == street_name


def test_ac_cannot_edit_incidents_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        inc = Incident.query.except_(Incident.query.filter_by(department_id=AC_DEPT)).first()
        new_date = datetime(2017, 6, 25, 1, 45)
        street_name = 'Not Allowed St'
        address_form = LocationForm(
            street_name=street_name,
            cross_street1='Your St',
            city='Boston',
            state='NH',
            zip_code='03435'
        )
        links_forms = [LinkForm(url=link.url, link_type=link.link_type).data for link in inc.links]
        license_plates_forms = [LicensePlateForm(number=lp.number, state=lp.state).data for lp in inc.license_plates]
        ooid_forms = [OOIdForm(ooid=officer.id) for officer in inc.officers]

        form = IncidentForm(
            date_field=str(new_date.date()),
            time_field=str(new_date.time()),
            report_number=inc.report_number,
            description=inc.description,
            department=AC_DEPT,
            address=address_form.data,
            links=links_forms,
            license_plates=license_plates_forms,
            officers=ooid_forms
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.incident_api', obj_id=inc.id) + '/edit',
            data=data,
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_admins_can_delete_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        incident = Incident.query.first()
        inc_id = incident.id
        rv = client.post(
            url_for('main.incident_api', obj_id=inc_id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Incident.query.get(inc_id)
        assert deleted is None


def test_acs_can_delete_incidents_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.filter_by(department_id=AC_DEPT).first()
        inc_id = incident.id
        rv = client.post(
            url_for('main.incident_api', obj_id=inc_id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 200
        deleted = Incident.query.get(inc_id)
        assert deleted is None


def test_acs_cannot_delete_incidents_not_in_their_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.except_(Incident.query.filter_by(department_id=AC_DEPT)).first()
        inc_id = incident.id
        rv = client.post(
            url_for('main.incident_api', obj_id=inc_id) + '/delete',
            follow_redirects=True
        )
        assert rv.status_code == 403
        not_deleted = Incident.query.get(inc_id)
        assert not_deleted.id is inc_id


def test_acs_can_get_edit_form_for_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.filter_by(department_id=AC_DEPT).first()
        rv = client.get(
            url_for('main.incident_api', obj_id=incident.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 200
        assert 'Update' in rv.data.decode('utf-8')


def test_acs_cannot_get_edit_form_for_their_non_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        incident = Incident.query.except_(Incident.query.filter_by(department_id=AC_DEPT)).first()
        rv = client.get(
            url_for('main.incident_api', obj_id=incident.id) + '/edit',
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_users_can_view_incidents_by_department(mockdata, client, session):
    with current_app.test_request_context():
        department = Department.query.first()
        department_incidents = Incident.query.filter_by(department_id=department.id)
        non_department_incidents = Incident.query.except_(Incident.query.filter_by(department_id=department.id))
        rv = client.get(
            url_for('main.incident_api', department_id=department.id))

        # Requires that report numbers in test data not include other report numbers
        # Tests for report numbers in table formatting, because testing for the raw report number can get false positives due to html encoding
        for incident in department_incidents:
            assert '<td>{}</td>'.format(incident.report_number) in rv.data.decode('utf-8')
        for incident in non_department_incidents:
            assert '<td>{}</td>'.format(incident.report_number) not in rv.data.decode('utf-8')


def test_admins_can_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        rv = client.get(url_for('main.incident_api', obj_id=1))
        assert 'Creator' in rv.data.decode('utf-8')


def test_acs_cannot_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        rv = client.get(url_for('main.incident_api', obj_id=1))
        assert 'Creator' not in rv.data.decode('utf-8')


def test_users_cannot_see_who_created_incidents(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        rv = client.get(url_for('main.incident_api', obj_id=1))
        assert 'Creator' not in rv.data.decode('utf-8')


def test_form_with_officer_id_prepopulates(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer_id = '1234'
        rv = client.get(url_for('main.incident_api') + 'new?officer_id={}'.format(officer_id))
        assert officer_id in rv.data.decode('utf-8')
