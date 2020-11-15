from flask import current_app

from OpenOversight.app.models import Department
from OpenOversight.tests.conftest import INACTIVE_DEPT_NAME

from .route_helpers import login_admin


def test_user_only_sees_active_departments_on_submit_images_page(mockdata, client, session):
    depts = Department.query.filter_by(is_active=True).all()

    with current_app.test_request_context():
        rv = client.get('/submit')

        result = rv.data.decode('utf-8')

        for dept in depts:
            assert dept.name in result
        assert INACTIVE_DEPT_NAME not in result


def test_admin_sees_all_departments_on_submit_images_page(mockdata, client, session):
    depts = Department.query.all()

    with current_app.test_request_context():
        login_admin(client)
        rv = client.get('/submit')

        result = rv.data.decode('utf-8')

        for dept in depts:
            assert dept.name in result
