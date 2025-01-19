from http import HTTPMethod
from typing import List

from flask import Blueprint, Response, jsonify
from sqlalchemy.orm import contains_eager

from OpenOversight.app.models.database import (
    BaseModel,
    Department,
    Description,
    Incident,
    Link,
    Officer,
    db,
)
from OpenOversight.app.models.database_cache import (
    get_database_cache_entry,
    put_database_cache_entry,
)
from OpenOversight.app.utils.constants import (
    KEY_DEPT_ALL_INCIDENTS,
    KEY_DEPT_ALL_LINKS,
    KEY_DEPT_ALL_NOTES,
)
from OpenOversight.app.utils.flask import limiter


v1 = Blueprint("v1", __name__, url_prefix="/api/v1")


def objs_to_dicts_jsonify(obj_list: List[BaseModel]) -> Response:
    return jsonify([o.to_dict() for o in obj_list])


@v1.route("/departments/<int:department_id>/officers", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_officers(department_id: int) -> Response:
    officers = Department.get_officers(department_id)
    return objs_to_dicts_jsonify(officers)


@v1.route("/departments/<int:department_id>/assignments", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_assignments(department_id: int) -> Response:
    assignments = Department.get_assignments(department_id)
    return objs_to_dicts_jsonify(assignments)


@v1.route("/departments/<int:department_id>/incidents", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_incidents(department_id: int) -> Response:
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_INCIDENTS)
    incidents = get_database_cache_entry(*cache_params)

    if incidents is None:
        incidents = Incident.query.filter_by(department_id=department_id).all()
        put_database_cache_entry(*cache_params, incidents)

    return objs_to_dicts_jsonify(incidents)


@v1.route("/departments/<int:department_id>/salaries", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_salaries(department_id: int) -> Response:
    salaries = Department.get_salaries(department_id)
    return objs_to_dicts_jsonify(salaries)


@v1.route("/departments/<int:department_id>/links", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_links(department_id: int) -> Response:
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_LINKS)
    links = get_database_cache_entry(*cache_params)

    if links is None:
        links = (
            db.session.query(Link)
            .join(Link.officers)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Link.officers))
            .all()
        )
        put_database_cache_entry(*cache_params, links)

    return objs_to_dicts_jsonify(links)


@v1.route("/departments/<int:department_id>/descriptions", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_descriptions(department_id: int) -> Response:
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_NOTES)
    notes = get_database_cache_entry(*cache_params)

    if notes is None:
        notes = (
            db.session.query(Description)
            .join(Description.officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Description.officer))
            .all()
        )
        put_database_cache_entry(*cache_params, notes)

    return objs_to_dicts_jsonify(notes)
