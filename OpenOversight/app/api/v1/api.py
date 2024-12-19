import json
from http import HTTPMethod, HTTPStatus

from flask import Blueprint, current_app
from sqlalchemy.orm import joinedload

from OpenOversight.app.models.database import Assignment, Department, Officer, db
from OpenOversight.app.models.database_cache import (
    get_database_cache_entry,
    put_database_cache_entry,
)
from OpenOversight.app.utils.constants import KEY_DEPT_ALL_OFFICERS


v1 = Blueprint("v1", __name__, url_prefix="/v1")


@v1.route("/departments/<int:department_id>/officers", methods=[HTTPMethod.GET])
def download_dept_officers(department_id: int):
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_OFFICERS)
    officers = get_database_cache_entry(*cache_params)
    if officers is None:
        officers = (
            db.session.query(Officer)
            .options(joinedload(Officer.assignments).joinedload(Assignment.job))
            .options(joinedload(Officer.salaries))
            .filter_by(department_id=department_id)
            .all()
        )
        put_database_cache_entry(*cache_params, officers)

    return current_app.response_class(
        mimetype="application/json",
        response=json.dumps(officers),
        status=HTTPStatus.OK,
    )
