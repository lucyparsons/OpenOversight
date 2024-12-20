from http import HTTPMethod

from flask import Blueprint, jsonify
from sqlalchemy.orm import contains_eager, joinedload

from OpenOversight.app.models.database import (
    Assignment,
    Department,
    Description,
    Incident,
    Link,
    Officer,
    Salary,
    db,
)
from OpenOversight.app.models.database_cache import (
    get_database_cache_entry,
    put_database_cache_entry,
)
from OpenOversight.app.utils.constants import (
    KEY_DEPT_ALL_ASSIGNMENTS,
    KEY_DEPT_ALL_INCIDENTS,
    KEY_DEPT_ALL_LINKS,
    KEY_DEPT_ALL_NOTES,
    KEY_DEPT_ALL_OFFICERS,
    KEY_DEPT_ALL_SALARIES,
)
from OpenOversight.app.utils.flask import limiter


v1 = Blueprint("v1", __name__, url_prefix="/api/v1")


def objs_to_dicts_jsonify(obj_list):
    return jsonify([o.to_dict() for o in obj_list])


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

    return objs_to_dicts_jsonify(officers)


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

    return objs_to_dicts_jsonify(assignments)


@v1.route("/departments/<int:department_id>/incidents", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_incidents(department_id: int):
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_INCIDENTS)
    incidents = get_database_cache_entry(*cache_params)

    if incidents is None:
        incidents = Incident.query.filter_by(department_id=department_id).all()
        put_database_cache_entry(*cache_params, incidents)

    return objs_to_dicts_jsonify(incidents)


@v1.route("/departments/<int:department_id>/salaries", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_salaries(department_id: int):
    cache_params = (Department(id=department_id), KEY_DEPT_ALL_SALARIES)
    salaries = get_database_cache_entry(*cache_params)

    if salaries is None:
        salaries = (
            db.session.query(Salary)
            .join(Salary.officer)
            .filter(Officer.department_id == department_id)
            .options(contains_eager(Salary.officer))
            .all()
        )
        put_database_cache_entry(*cache_params, salaries)

    return objs_to_dicts_jsonify(salaries)


@v1.route("/departments/<int:department_id>/links", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def get_dept_links(department_id: int):
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
def get_dept_descriptions(department_id: int):
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
