import json
from http import HTTPMethod, HTTPStatus

from flask import Blueprint, current_app
from sqlalchemy.orm import contains_eager, joinedload

from OpenOversight.app.models.database import Assignment, Department, Officer, db
from OpenOversight.app.models.database_cache import (
    get_database_cache_entry,
    put_database_cache_entry,
)
from OpenOversight.app.utils.constants import (
    KEY_DEPT_ALL_ASSIGNMENTS,
    KEY_DEPT_ALL_OFFICERS,
)
from OpenOversight.app.utils.flask import limiter


v1 = Blueprint("v1", __name__, url_prefix="/api/v1")


@v1.route("/departments/<int:department_id>/officers", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_officers(department_id: int):
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


@v1.route("/departments/<int:department_id>/assignments", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_assignments(department_id: int):
    cache_params = Department(id=department_id), KEY_DEPT_ALL_ASSIGNMENTS
    assignments = get_database_cache_entry(*cache_params)
    if assignments is None:
        assignments = (
            db.session.query(Assignment)
            .join(Assignment.base_officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Assignment.base_officer))
            .options(joinedload(Assignment.unit))
            .options(joinedload(Assignment.job))
            .all()
        )
        put_database_cache_entry(*cache_params, assignments)

    return current_app.response_class(
        mimetype="application/json",
        response=json.dumps(assignments),
        status=HTTPStatus.OK,
    )
