import json
from http import HTTPStatus

import pytest
from flask import current_app, url_for
from sqlalchemy.orm import contains_eager, joinedload

from OpenOversight.app.models.database import Assignment, Officer
from OpenOversight.app.utils.constants import ENCODING_UTF_8


@pytest.mark.parametrize("department_id", [1, 3000])
def test_get_dept_officers(client, department_id: int):
    with current_app.test_request_context():
        expected_offices = Officer.query.filter_by(department_id=department_id).all()

        resp = client.get(
            url_for("v1.get_dept_officers", department_id=department_id),
            follow_recirects=False,
        )
        officers = json.loads(resp.data.decode(ENCODING_UTF_8))

        assert resp.status_code == HTTPStatus.OK
        assert len(officers) == len(expected_offices)


@pytest.mark.parametrize("department_id", [1, 3000])
def test_get_dept_assignments(client, session, department_id: int):
    with current_app.test_request_context():
        expected_assignments = (
            session.get(Assignment)
            .join(Assignment.base_officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Assignment.base_officer))
            .options(joinedload(Assignment.unit))
            .options(joinedload(Assignment.job))
            .all()
        )

        resp = client.get(
            url_for("v1.get_dept_assignments", department_id=department_id),
            follow_recirects=False,
        )
        assignments = json.loads(resp.data.decode(ENCODING_UTF_8))

        assert resp.status_code == HTTPStatus.OK
        assert len(assignments) == len(expected_assignments)
