from flask import current_app, url_for

from OpenOversight.app.main.forms import (ChangeDepartmentStatusForm,
                                          EditDepartmentForm)
from OpenOversight.app.models import Department
from OpenOversight.tests.conftest import AC_DEPT, INACTIVE_DEPT_NAME

from .route_helpers import login_ac, login_admin, login_user


def test_user_cannot_access_departments_api(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(url_for('main.department_api'),
                        follow_redirects=True)

        assert rv.status_code == 403


def test_admin_can_access_departments_api(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(url_for('main.department_api'),
                        follow_redirects=True)

        assert rv.status_code == 200


def test_admin_can_edit_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        dept = Department.query.all()[0]
        dept_id = dept.id

        form = EditDepartmentForm(name="New Name",
                                  short_name="NAW")

        rv = client.post(
            url_for('main.department_api', department_id=dept_id) + '/edit',
            data=form.data,
            follow_redirects=True
        )

        assert '{} has been updated!'.format("New Name") in rv.data.decode('utf-8')

        dept = Department.query.get(dept_id)
        assert dept.name == "New Name"
        assert dept.short_name == "NAW"


def test_ac_cannot_edit_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        dept = Department.query.all()[0]
        dept_id = dept.id

        form = EditDepartmentForm(name="Fake Police Department",
                                  short_name="FPD", is_active=False)

        rv = client.post(
            url_for('main.department_api', department_id=dept_id) + '/edit',
            data=form.data,
            follow_redirects=True
        )

        assert rv.status_code == 403


def test_admin_cannot_change_department_name_to_existing_department_name(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        dept = Department.query.all()[0]
        dept_id = dept.id
        dept_name = dept.name

        form = EditDepartmentForm(name="Candy Kingdom Police Department",
                                  short_name="CKPD", is_active=False)

        rv = client.post(
            url_for('main.department_api', department_id=dept_id) + '/edit',
            data=form.data,
            follow_redirects=True
        )

        assert '{} already exists'.format(form.data['name']) in rv.data.decode('utf-8')

        dept = Department.query.get(dept_id)
        assert dept.name == dept_name


def test_admin_can_disable_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        dept = Department.query.filter_by(is_active=True).first()
        dept_id = dept.id
        dept_name = dept.name

        assert dept.is_active

        rv = client.get(
            url_for('main.department_api', department_id=dept_id) + '/disable',
            follow_redirects=True
        )

        assert '{} has been disabled!'.format(dept_name) in rv.data.decode('utf-8')

        dept = Department.query.get(dept_id)
        assert not dept.is_active


def test_admin_can_enable_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        dept = Department.query.filter_by(is_active=False).first()
        dept_id = dept.id
        dept_name = dept.name

        assert not dept.is_active

        rv = client.get(
            url_for('main.department_api', department_id=dept_id) + '/enable',
            follow_redirects=True
        )

        assert '{} has been enabled!'.format(dept_name) in rv.data.decode('utf-8')

        dept = Department.query.get(dept_id)
        assert dept.is_active


def test_admin_can_delete_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        depts = Department.query.all()
        dept = Department.query.all()[0]
        dept_id = dept.id
        dept_name = dept.name

        rv = client.post(
            url_for('main.department_api', department_id=dept_id) + '/delete',
            follow_redirects=True
        )

        assert '{} has been deleted!'.format(dept_name) in rv.data.decode('utf-8')

        current_depts = Department.query.all()
        assert len(current_depts) == len(depts) - 1


def test_area_coordinator_can_access_department_page(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        rv = client.get(
            url_for('main.view_ac_dept'),
            follow_redirects=True
        )

        assert rv.status_code == 200


def test_area_coordinator_can_disable_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        form = ChangeDepartmentStatusForm(is_active=False)
        rv = client.post(url_for('main.view_ac_dept'),
                         data=form.data,
                         follow_redirects=True)

        assert 'Updated!' in rv.data.decode('utf-8')
        dept = Department.query.get(AC_DEPT)
        assert not dept.is_active


def test_area_coordinator_can_enable_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        dept = Department.query.get(AC_DEPT)
        dept.is_active = False

        form = ChangeDepartmentStatusForm(is_active=True)
        rv = client.post(url_for('main.view_ac_dept'),
                         data=form.data,
                         follow_redirects=True)

        assert 'Updated!' in rv.data.decode('utf-8')
        dept = Department.query.get(AC_DEPT)
        assert dept.is_active


def test_admin_can_see_all_departments_on_find_officer_page(mockdata, client, session):
    depts = Department.query.all()

    with current_app.test_request_context():
        login_admin(client)

        rv = client.get('/find')

        result = rv.data.decode('utf-8')

        for dept in depts:
            assert dept.name in result


def test_user_only_sees_active_departments_on_find_officer_page(mockdata, client, session):
    depts = Department.query.filter_by(is_active=True).all()

    with current_app.test_request_context():
        rv = client.get('/find')

        result = rv.data.decode('utf-8')

        for dept in depts:
            assert dept.name in result
        assert INACTIVE_DEPT_NAME not in result
