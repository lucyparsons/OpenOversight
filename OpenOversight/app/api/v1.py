from http import HTTPMethod

from flask import Blueprint, Response, jsonify
from sqlalchemy.orm import Query

from OpenOversight.app.models.database import Department
from OpenOversight.app.utils.flask import limiter


v1 = Blueprint("v1", __name__, url_prefix="/api/v1")


def objs_to_dicts_jsonify(obj_list: Query) -> Response:
    return jsonify([o.to_dict() for o in obj_list])


@v1.route("/departments/<int:department_id>/assignments", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_assignments(department_id: int) -> Response:
    assignments = Department.get_assignments(department_id)
    return objs_to_dicts_jsonify(assignments)


@v1.route("/departments/<int:department_id>/descriptions", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_descriptions(department_id: int) -> Response:
    descriptions = Department.get_descriptions(department_id)
    return objs_to_dicts_jsonify(descriptions)


@v1.route("/departments/<int:department_id>/incidents", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_incidents(department_id: int) -> Response:
    incidents = Department.get_incidents(department_id)
    return objs_to_dicts_jsonify(incidents)


@v1.route("/departments/<int:department_id>/links", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_links(department_id: int) -> Response:
    links = Department.get_links(department_id)
    return objs_to_dicts_jsonify(links)


@v1.route("/departments/<int:department_id>/officers", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_officers(department_id: int) -> Response:
    officers = Department.get_officers(department_id)
    return objs_to_dicts_jsonify(officers)


@v1.route("/departments/<int:department_id>/salaries", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_salaries(department_id: int) -> Response:
    salaries = Department.get_salaries(department_id)
    return objs_to_dicts_jsonify(salaries)
