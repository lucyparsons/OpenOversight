import json
from http import HTTPStatus

import pytest
from flask import current_app, url_for
from sqlalchemy.orm import contains_eager, joinedload

from OpenOversight.app.models.database import Assignment, Incident, Officer, Salary
from OpenOversight.app.utils.constants import ENCODING_UTF_8


@pytest.mark.parametrize("department_id", [1, 3000])
def test_get_dept_attributes(client, session, department_id: int):
    with current_app.test_request_context():
        # Get officers
        expected_officers = Officer.query.filter_by(department_id=department_id).count()

        resp_officers = client.get(
            url_for("v1.get_dept_officers", department_id=department_id),
            follow_redirects=True,
        )
        officers = json.loads(resp_officers.data.decode(ENCODING_UTF_8))

        assert resp_officers.status_code == HTTPStatus.OK
        assert len(officers) == expected_officers

        # Get assignments
        expected_assignments = (
            session.get(Assignment)
            .join(Assignment.base_officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Assignment.base_officer))
            .options(joinedload(Assignment.unit))
            .options(joinedload(Assignment.job))
            .all()
        )

        resp_assignments = client.get(
            url_for("v1.get_dept_assignments", department_id=department_id),
            follow_redirects=True,
        )
        assignments = json.loads(resp_assignments.data.decode(ENCODING_UTF_8))

        assert resp_assignments.status_code == HTTPStatus.OK
        assert len(assignments) == len(expected_assignments)

        # Get incidents
        expected_incidents = Incident.query.filter_by(
            department_id=department_id
        ).count()

        resp_incidents = client.get(
            url_for("v1.get_dept_incidents", department_id=department_id),
            follow_redirects=True,
        )
        incidents = json.loads(resp_incidents.data.decode(ENCODING_UTF_8))

        assert resp_assignments.status_code == HTTPStatus.OK
        assert len(incidents) == expected_incidents

        # Get salaries
        expected_salaries = (
            session.query(Salary)
            .join(Salary.officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Salary.officer))
            .count()
        )

        resp_salaries = client.get(
            url_for("v1.get_dept_salaries", department_id=department_id),
            follow_redirects=True,
        )
        salaries = json.loads(resp_salaries.data.decode(ENCODING_UTF_8))

        assert resp_assignments.status_code == HTTPStatus.OK
        assert len(salaries) == expected_salaries
