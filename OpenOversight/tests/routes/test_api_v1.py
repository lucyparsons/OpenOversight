import json
from http import HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.models.database import Officer
from OpenOversight.app.utils.constants import ENCODING_UTF_8


@pytest.mark.parametrize("department_id", [1, 3000])
def test_get_dept_officers(client, session, department_id: int):
    with current_app.test_request_context():
        expected_offices = Officer.query.filter_by(department_id=department_id).all()

        resp = client.get(
            url_for("v1.get_dept_officers", department_id=department_id),
            follow_recirects=False,
        )
        officers = json.loads(resp.data.decode(ENCODING_UTF_8))

        assert resp.status_code == HTTPStatus.OK
        assert len(officers) == len(expected_offices)
