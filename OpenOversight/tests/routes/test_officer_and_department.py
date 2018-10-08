# Routing and view tests
import pytest
import random
from flask import url_for, current_app
from ..conftest import AC_DEPT
from OpenOversight.app.utils import dept_choices
from OpenOversight.app.main.choices import RACE_CHOICES, GENDER_CHOICES
from .route_helpers import login_admin, login_ac, process_form_data


from OpenOversight.app.main.forms import (AssignmentForm, DepartmentForm,
                                          AddOfficerForm, AddUnitForm,
                                          EditOfficerForm, LinkForm,
                                          EditDepartmentForm,)

from OpenOversight.app.models import Department, Unit, Officer


@pytest.mark.parametrize("route", [
    ('/submit'),
    ('/label'),
    ('/department/1'),
    ('/officer/3'),
    ('/complaint?officer_star=1901&officer_first_name=HUGH&officer_last_name=BUTZ&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png')
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route", [
    ('/sort/department/1'),
    ('/cop_face/department/1'),
    ('/department/new'),
    ('/officer/new'),
    ('/unit/new'),
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


# POST-only routes
@pytest.mark.parametrize("route", [
    ('/officer/3/assignment/new'),
])
def test_route_post_only(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 405


def test_user_can_access_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(
            url_for('main.officer_profile', officer_id=3),
            follow_redirects=True
        )
        assert 'Officer Detail' in rv.data


def test_user_can_access_officer_list(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(
            url_for('main.list_officer', department_id=2)
        )

        assert 'Officers' in rv.data


def test_ac_can_access_admin_on_dept_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()

        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        assert 'Admin only' in rv.data


def test_ac_cannot_access_admin_on_non_dept_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()

        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )
        assert 'Admin only' not in rv.data


def test_admin_can_add_officer_badge_number(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        form = AssignmentForm(star_no='1234',
                              rank='COMMANDER')

        rv = client.post(
            url_for('main.add_assignment', officer_id=3),
            data=form.data,
            follow_redirects=True
        )

        assert 'Added new assignment' in rv.data


def test_ac_can_add_officer_badge_number_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = AssignmentForm(star_no='S1234',
                              rank='COMMANDER')
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()

        rv = client.post(
            url_for('main.add_assignment', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert 'Added new assignment' in rv.data

        # test that assignment exists in database
        assignment = Officer.query.filter(Officer.assignments.any(star_no='S1234'))
        assert assignment is not None


def test_ac_cannot_add_non_dept_officer_badge(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = AssignmentForm(star_no='1234',
                              rank='COMMANDER')
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()

        rv = client.post(
            url_for('main.add_assignment', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 403


def test_admin_can_edit_officer_badge_number(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        form = AssignmentForm(star_no='1234',
                              rank='COMMANDER')

        rv = client.post(
            url_for('main.officer_profile', officer_id=3),
            data=form.data,
            follow_redirects=True
        )

        form = AssignmentForm(star_no='12345')
        officer = Officer.query.filter_by(id=3).one()

        rv = client.post(
            url_for('main.edit_assignment', officer_id=officer.id,
                    assignment_id=officer.assignments[0].id,
                    form=form),
            data=form.data,
            follow_redirects=True
        )

        assert 'Edited officer assignment' in rv.data
        assert officer.assignments[0].star_no == '12345'


def test_ac_can_edit_officer_in_their_dept_badge_number(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        star_no = '1234'
        new_star_no = '12345'
        officer = Officer.query.filter_by(department_id=AC_DEPT).first()
        form = AssignmentForm(star_no=star_no,
                              rank='COMMANDER')

        rv = client.post(
            url_for('main.officer_profile', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        form = AssignmentForm(star_no=new_star_no)
        officer = Officer.query.filter_by(id=officer.id).one()

        rv = client.post(
            url_for('main.edit_assignment', officer_id=officer.id,
                    assignment_id=officer.assignments[0].id,
                    form=form),
            data=form.data,
            follow_redirects=True
        )

        assert 'Edited officer assignment' in rv.data
        assert officer.assignments[0].star_no == new_star_no


def test_ac_cannot_edit_officer_outside_their_dept_badge_number(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        star_no = '1234'
        new_star_no = '12345'
        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        form = AssignmentForm(star_no=star_no,
                              rank='COMMANDER')

        rv = client.post(
            url_for('main.officer_profile', officer_id=officer.id),
            data=form.data,
            follow_redirects=True
        )

        form = AssignmentForm(star_no=new_star_no)
        officer = Officer.query.filter_by(id=officer.id).one()

        rv = client.post(
            url_for('main.edit_assignment', officer_id=officer.id,
                    assignment_id=officer.assignments[0].id,
                    form=form),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 403


def test_admin_can_add_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        form = DepartmentForm(name='Test Police Department',
                              short_name='TPD')

        rv = client.post(
            url_for('main.add_department'),
            data=form.data,
            follow_redirects=True
        )

        assert 'New department' in rv.data

        # Check the department was added to the database
        department = Department.query.filter_by(
            name='Test Police Department').one()
        assert department.short_name == 'TPD'


def test_ac_cannot_add_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = DepartmentForm(name='Test Police Department',
                              short_name='TPD')

        rv = client.post(
            url_for('main.add_department'),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 403


def test_admin_cannot_add_duplicate_police_department(mockdata, client,
                                                      session):
    with current_app.test_request_context():
        login_admin(client)

        form = DepartmentForm(name='Chicago Police Department',
                              short_name='CPD')

        rv = client.post(
            url_for('main.add_department'),
            data=form.data,
            follow_redirects=True
        )

        # Try to add the same police department again
        rv = client.post(
            url_for('main.add_department'),
            data=form.data,
            follow_redirects=True
        )

        assert 'already exists' in rv.data

        # Check that only one department was added to the database
        # one() method will throw exception if more than one department found
        department = Department.query.filter_by(
            name='Chicago Police Department').one()
        assert department.short_name == 'CPD'


def test_admin_can_edit_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        misspelled_form = DepartmentForm(name='Misspelled Police Department',
                                         short_name='MPD')

        misspelled_rv = client.post(
            url_for('main.add_department'),
            data=misspelled_form.data,
            follow_redirects=True
        )

        assert 'New department' in misspelled_rv.data

        department = Department.query.filter_by(name='Misspelled Police Department').one()

        corrected_form = EditDepartmentForm(name='Corrected Police Department',
                                            short_name='MPD')

        corrected_rv = client.post(
            url_for('main.edit_department', department_id=department.id),
            data=corrected_form.data,
            follow_redirects=True
        )

        assert 'Department Corrected Police Department edited' in corrected_rv.data

        # Check the department with the new name is now in the database.
        corrected_department = Department.query.filter_by(
            name='Corrected Police Department').one()
        assert corrected_department.short_name == 'MPD'

        # Check that the old name is no longer present:
        assert Department.query.filter_by(
            name='Misspelled Police Department').count() == 0

        edit_short_name_form = EditDepartmentForm(name='Corrected Police Department',
                                                  short_name='CPD')

        edit_short_name_rv = client.post(
            url_for('main.edit_department', department_id=department.id),
            data=edit_short_name_form.data,
            follow_redirects=True
        )

        assert 'Department Corrected Police Department edited' in edit_short_name_rv.data

        edit_short_name_department = Department.query.filter_by(
            name='Corrected Police Department').one()
        assert edit_short_name_department.short_name == 'CPD'


def test_ac_cannot_edit_police_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.first()

        form = EditDepartmentForm(name='Corrected Police Department',
                                  short_name='CPD')

        rv = client.post(
            url_for('main.edit_department', department_id=department.id),
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 403


def test_admin_cannot_duplicate_police_department_during_edit(mockdata, client,
                                                              session):
    with current_app.test_request_context():
        login_admin(client)

        existing_dep_form = DepartmentForm(name='Existing Police Department',
                                           short_name='EPD')

        existing_dep_rv = client.post(
            url_for('main.add_department'),
            data=existing_dep_form.data,
            follow_redirects=True
        )

        assert 'New department' in existing_dep_rv.data

        new_dep_form = DepartmentForm(name='New Police Department',
                                      short_name='NPD')

        new_dep_rv = client.post(
            url_for('main.add_department'),
            data=new_dep_form.data,
            follow_redirects=True
        )

        assert 'New department' in new_dep_rv.data

        new_department = Department.query.filter_by(
            name='New Police Department').one()

        edit_form = EditDepartmentForm(name='Existing Police Department',
                                       short_name='EPD2')

        rv = client.post(
            url_for('main.edit_department', department_id=new_department.id),
            data=edit_form.data,
            follow_redirects=True
        )

        assert 'already exists' in rv.data

        # make sure original department is still here
        existing_department = Department.query.filter_by(
            name='Existing Police Department').one()
        assert existing_department.short_name == 'EPD'

        # make sure new department is left unchanged
        new_department = Department.query.filter_by(
            name='New Police Department').one()
        assert new_department.short_name == 'NPD'


def test_expected_dept_appears_in_submission_dept_selection(mockdata, client,
                                                            session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(
            url_for('main.submit_data'),
            follow_redirects=True
        )

        assert 'Springfield Police Department' in rv.data


def test_admin_can_add_new_officer(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        department = random.choice(dept_choices())
        links = [
            LinkForm(url='http://www.pleasework.com', link_type='link').data,
            LinkForm(url='http://www.avideo/?v=2345jk', link_type='video').data
        ]
        form = AddOfficerForm(first_name='Test',
                              last_name='McTesterson',
                              middle_initial='T',
                              race='WHITE',
                              gender='M',
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              links=links)

        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        assert 'McTesterson' in rv.data

        # Check the officer was added to the database
        officer = Officer.query.filter_by(
            last_name='McTesterson').one()
        assert officer.first_name == 'Test'
        assert officer.race == 'WHITE'
        assert officer.gender == 'M'


def test_ac_can_add_new_officer_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.filter_by(id=AC_DEPT).first()
        first_name = 'Testy'
        last_name = 'OTester'
        middle_initial = 'R'
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        form = AddOfficerForm(first_name=first_name,
                              last_name=last_name,
                              middle_initial=middle_initial,
                              race=race,
                              gender=gender,
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              # because of encoding error, link_type must be set for tests
                              links=[LinkForm(link_type='link').data])

        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        assert rv.status_code == 200
        assert last_name in rv.data

        # Check the officer was added to the database
        officer = Officer.query.filter_by(
            last_name=last_name).one()
        assert officer.first_name == first_name
        assert officer.race == race
        assert officer.gender == gender


def test_ac_cannot_add_new_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.except_(Department.query.filter_by(id=AC_DEPT)).first()
        first_name = 'Sam'
        last_name = 'Augustus'
        middle_initial = 'H'
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        form = AddOfficerForm(first_name=first_name,
                              last_name=last_name,
                              middle_initial=middle_initial,
                              race=race,
                              gender=gender,
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              # because of encoding error, link_type must be set for tests
                              links=[LinkForm(link_type='link').data])

        data = process_form_data(form.data)

        client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        officer = Officer.query.filter_by(last_name=last_name).first()
        assert officer is None


def test_admin_can_edit_existing_officer(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        department = random.choice(dept_choices())
        link_url0 = 'http://pleasework.com'
        link_url1 = 'http://avideo/?v=2345jk'
        links = [
            LinkForm(url=link_url0, link_type='link').data,
            LinkForm(url=link_url0, link_type='video').data
        ]
        form = AddOfficerForm(first_name='Test',
                              last_name='Testerinski',
                              middle_initial='T',
                              race='WHITE',
                              gender='M',
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              links=links)
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        officer = Officer.query.filter_by(
            last_name='Testerinski').one()

        form = EditOfficerForm(last_name='Changed', links=links[:1])
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.edit_officer', officer_id=officer.id),
            data=data,
            follow_redirects=True
        )

        assert 'Changed' in rv.data
        assert 'Testerinski' not in rv.data
        assert link_url0 in rv.data
        assert link_url1 not in rv.data


def test_ac_cannot_edit_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()
        old_last_name = officer.last_name

        new_last_name = 'Shiny'
        form = EditOfficerForm(
            last_name=new_last_name,
            # because of encoding error, link_type must be set for tests
            links=[LinkForm(link_type='link').data])

        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.edit_officer', officer_id=officer.id),
            data=data,
            follow_redirects=True
        )

        assert rv.status_code == 403

        # Ensure changes were not made to database
        officer = Officer.query.filter_by(
            id=officer.id).one()
        assert officer.last_name == old_last_name


def test_ac_can_see_officer_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        officer = Officer.query.except_(Officer.query.filter_by(department_id=AC_DEPT)).first()

        rv = client.get(
            url_for('main.officer_profile', officer_id=officer.id),
            follow_redirects=True
        )

        assert rv.status_code == 200
        # Testing names doesn't work bc the way we display them varies
        assert str(officer.id) in rv.data


def test_ac_can_edit_officer_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        department = Department.query.filter_by(id=AC_DEPT).first()
        first_name = 'Testier'
        last_name = 'OTester'
        middle_initial = 'R'
        suffix = ''
        race = random.choice(RACE_CHOICES)[0]
        gender = random.choice(GENDER_CHOICES)[0]
        form = AddOfficerForm(first_name=first_name,
                              last_name=last_name,
                              middle_initial=middle_initial,
                              suffix=suffix,
                              race=race,
                              gender=gender,
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              # because of encoding error, link_type must be set for tests
                              links=[LinkForm(link_type='link').data])

        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        officer = Officer.query.filter_by(
            last_name=last_name).one()

        new_last_name = 'Shiny'
        form = EditOfficerForm(
            first_name=first_name,
            last_name=new_last_name,
            suffix=suffix,
            race=race,
            gender=gender,
            department=department.id,
            # because of encoding error, link_type must be set for tests
            links=[LinkForm(link_type='link').data]
        )
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.edit_officer', officer_id=officer.id),
            data=data,
            follow_redirects=True
        )

        assert new_last_name in rv.data
        assert last_name not in rv.data

        # Check the changes were added to the database
        officer = Officer.query.filter_by(
            id=officer.id).one()
        assert officer.last_name == new_last_name


def test_admin_adds_officer_without_middle_initial(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        department = random.choice(dept_choices())
        form = AddOfficerForm(first_name='Test',
                              last_name='McTesty',
                              race='WHITE',
                              gender='M',
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              # because of encoding error, link_type must be set for tests
                              links=[LinkForm(link_type='link').data])
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        assert 'McTesty' in rv.data

        # Check the officer was added to the database
        officer = Officer.query.filter_by(
            last_name='McTesty').one()
        assert officer.first_name == 'Test'
        assert officer.middle_initial == ''
        assert officer.race == 'WHITE'
        assert officer.gender == 'M'


def test_admin_adds_officer_with_letter_in_badge_no(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        department = random.choice(dept_choices())
        form = AddOfficerForm(first_name='Test',
                              last_name='Testersly',
                              middle_initial='T',
                              race='WHITE',
                              gender='M',
                              star_no='T666',
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              # because of encoding error, link_type must be set for tests
                              links=[LinkForm(link_type='link').data])
        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        assert 'Testersly' in rv.data

        # Check the officer was added to the database
        officer = Officer.query.filter_by(
            last_name='Testersly').one()
        assert officer.first_name == 'Test'
        assert officer.race == 'WHITE'
        assert officer.gender == 'M'
        assert officer.assignments[0].star_no == 'T666'


def test_admin_can_add_new_unit(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        department = Department.query.filter_by(
            name='Springfield Police Department').first()
        form = AddUnitForm(descrip='Test', department=department.id)

        rv = client.post(
            url_for('main.add_unit'),
            data=form.data,
            follow_redirects=True
        )

        assert 'New unit' in rv.data

        # Check the unit was added to the database
        unit = Unit.query.filter_by(
            descrip='Test').one()
        assert unit.department_id == department.id


def test_ac_can_add_new_unit_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.filter_by(
            id=AC_DEPT).first()
        form = AddUnitForm(descrip='Test', department=department.id)

        rv = client.post(
            url_for('main.add_unit'),
            data=form.data,
            follow_redirects=True
        )

        assert 'New unit' in rv.data

        # Check the unit was added to the database
        unit = Unit.query.filter_by(
            descrip='Test').one()
        assert unit.department_id == department.id


def test_ac_cannot_add_new_unit_not_in_their_dept(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        department = Department.query.except_(Department.query.filter_by(id=AC_DEPT)).first()
        form = AddUnitForm(descrip='Test', department=department.id)

        client.post(
            url_for('main.add_unit'),
            data=form.data,
            follow_redirects=True
        )

        # Check the unit was not added to the database
        unit = Unit.query.filter_by(
            descrip='Test').first()
        assert unit is None


def test_admin_can_add_new_officer_with_suffix(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        department = random.choice(dept_choices())
        links = [
            LinkForm(url='http://www.pleasework.com', link_type='link').data,
            LinkForm(url='http://www.avideo/?v=2345jk', link_type='video').data
        ]
        form = AddOfficerForm(first_name='Testy',
                              last_name='McTesty',
                              middle_initial='T',
                              suffix='Jr',
                              race='WHITE',
                              gender='M',
                              star_no=666,
                              rank='COMMANDER',
                              department=department.id,
                              birth_year=1990,
                              links=links)

        data = process_form_data(form.data)

        rv = client.post(
            url_for('main.add_officer'),
            data=data,
            follow_redirects=True
        )

        assert 'McTesty' in rv.data

        # Check the officer was added to the database
        officer = Officer.query.filter_by(
            last_name='McTesty').one()
        assert officer.first_name == 'Testy'
        assert officer.race == 'WHITE'
        assert officer.gender == 'M'
        assert officer.suffix == 'Jr'


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
