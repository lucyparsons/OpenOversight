import csv
import io
from datetime import date
from typing import Any, Callable, Dict, List, TypeVar

from flask import Response, abort
from sqlalchemy.orm import Query

from OpenOversight.app.models.database import (
    Assignment,
    Department,
    Description,
    Incident,
    Link,
    Officer,
    Salary,
)


T = TypeVar("T")
_Record = Dict[str, Any]


########################################################################################
# Check util methods
########################################################################################


def check_output(output_str):
    if output_str == "Not Sure":
        return ""
    return output_str


########################################################################################
# Route assistance function
########################################################################################


def make_downloadable_csv(
    query: Query,
    department_id: int,
    csv_suffix: str,
    field_names: List[str],
    record_maker: Callable[[T], _Record],
) -> Response:
    department = Department.query.filter_by(id=department_id).first()
    if not department:
        abort(404)

    csv_output = io.StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=field_names)
    csv_writer.writeheader()

    for entity in query:
        record = record_maker(entity)
        csv_writer.writerow(record)

    dept_name = department.name.replace(" ", "_")
    csv_name = dept_name + "_" + csv_suffix + ".csv"

    csv_headers = {"Content-disposition": "attachment; filename=" + csv_name}
    return Response(csv_output.getvalue(), mimetype="text/csv", headers=csv_headers)


########################################################################################
# Record makers
########################################################################################


def salary_record_maker(salary: Salary) -> _Record:
    return {
        "id": salary.id,
        "officer id": salary.officer_id,
        "first name": salary.officer.first_name,
        "last name": salary.officer.last_name,
        "salary": salary.salary,
        "overtime_pay": salary.overtime_pay,
        "year": salary.year,
        "is_fiscal_year": salary.is_fiscal_year,
    }


def officer_record_maker(officer: Officer) -> _Record:
    if officer.assignments:
        most_recent_assignment = max(
            officer.assignments, key=lambda a: a.start_date or date.min
        )
        most_recent_title = most_recent_assignment.job and check_output(
            most_recent_assignment.job.job_title
        )
    else:
        most_recent_assignment = None
        most_recent_title = None
    if officer.salaries:
        most_recent_salary = max(officer.salaries, key=lambda s: s.year)
    else:
        most_recent_salary = None
    return {
        "id": officer.id,
        "unique identifier": officer.unique_internal_identifier,
        "last name": officer.last_name,
        "first name": officer.first_name,
        "middle initial": officer.middle_initial,
        "suffix": officer.suffix,
        "gender": check_output(officer.gender),
        "race": check_output(officer.race),
        "birth year": officer.birth_year,
        "employment date": officer.employment_date,
        "badge number": most_recent_assignment and most_recent_assignment.star_no,
        "job title": most_recent_title,
        "most recent salary": most_recent_salary and most_recent_salary.salary,
    }


def assignment_record_maker(assignment: Assignment) -> _Record:
    officer = assignment.base_officer
    return {
        "id": assignment.id,
        "officer id": assignment.officer_id,
        "officer unique identifier": officer and officer.unique_internal_identifier,
        "badge number": assignment.star_no,
        "job title": assignment.job and check_output(assignment.job.job_title),
        "start date": assignment.start_date,
        "end date": assignment.resign_date,
        "unit id": assignment.unit and assignment.unit.id,
        "unit description": assignment.unit and assignment.unit.description,
    }


def incidents_record_maker(incident: Incident) -> _Record:
    return {
        "id": incident.id,
        "report_num": incident.report_number,
        "date": incident.date,
        "time": incident.time,
        "description": incident.description,
        "location": incident.address,
        "licenses": " ".join(map(str, incident.license_plates)),
        "links": " ".join(map(str, incident.links)),
        "officers": " ".join(map(str, incident.officers)),
    }


def links_record_maker(link: Link) -> _Record:
    return {
        "id": link.id,
        "title": link.title,
        "url": link.url,
        "link_type": link.link_type,
        "description": link.description,
        "author": link.author,
        "officers": [officer.id for officer in link.officers],
        "incidents": [incident.id for incident in link.incidents],
    }


def descriptions_record_maker(description: Description) -> _Record:
    return {
        "id": description.id,
        "text_contents": description.text_contents,
        "created_by": description.created_by,
        "officer_id": description.officer_id,
        "created_at": description.created_at,
        "last_updated_at": description.last_updated_at,
    }
