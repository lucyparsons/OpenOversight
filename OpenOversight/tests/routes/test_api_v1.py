import pytest
from flask import current_app, url_for


@pytest.mark.parametrize("department_id", [1, 3000])
def test_get_dept_officers(client, department_id: int):
    with current_app.test_request_context():
        resp = client.get(
            url_for("v1.get_dept_officers", department_id=department_id),
            follow_recirects=False,
        )
        print(resp)
