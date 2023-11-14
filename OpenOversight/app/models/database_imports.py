from datetime import date, time
from typing import Any, Dict, Optional, Sequence, Tuple, Union

import dateutil.parser

from OpenOversight.app import login_manager
from OpenOversight.app.models.database import (
    Assignment,
    Incident,
    LicensePlate,
    Link,
    Location,
    Officer,
    Salary,
    User,
    db,
)
from OpenOversight.app.utils.choices import (
    GENDER_CHOICES,
    LINK_CHOICES,
    RACE_CHOICES,
    SUFFIX_CHOICES,
)
from OpenOversight.app.utils.general import get_or_create, str_is_true
from OpenOversight.app.validators import state_validator, url_validator


def validate_choice(
    value: Optional[str], given_choices: Sequence[Tuple[str, str]]
) -> Optional[str]:
    if value:
        for label, choice_value in given_choices:
            if value.lower() in [choice_value.lower(), label.lower()]:
                return label
        print(f"'{value}' no valid choice of {str(given_choices)}")
    return None


def parse_date(date_str: Optional[str]) -> Optional[date]:
    if date_str:
        return dateutil.parser.parse(date_str).date()
    return None


def parse_time(time_str: Optional[str]) -> Optional[time]:
    if time_str:
        return dateutil.parser.parse(time_str).time()
    return None


def parse_int(value: Optional[Union[str, int]]) -> Optional[int]:
    if value == 0 or value:
        return int(value)
    return None


def parse_float(value: Optional[Union[str, float]]) -> Optional[float]:
    if value == 0.0 or value:
        return float(value)
    return None


def parse_bool(value: Optional[str]) -> bool:
    if value:
        return str_is_true(value)
    return False


def parse_str(value: Optional[str], default: Optional[str] = "") -> Optional[str]:
    if value is None:
        return default
    return value.strip() or default


def create_officer_from_dict(data: Dict[str, Any], force_id: bool = False) -> Officer:
    admin_user = User.query.filter_by(is_administrator=True).first()

    officer = Officer(
        department_id=int(data["department_id"]),
        last_name=parse_str(data.get("last_name", "")),
        first_name=parse_str(data.get("first_name", "")),
        middle_initial=parse_str(data.get("middle_initial", "")),
        suffix=validate_choice(data.get("suffix", ""), SUFFIX_CHOICES),
        race=validate_choice(data.get("race"), RACE_CHOICES),
        gender=validate_choice(data.get("gender"), GENDER_CHOICES),
        employment_date=parse_date(data.get("employment_date")),
        birth_year=parse_int(data.get("birth_year")),
        unique_internal_identifier=parse_str(
            data.get("unique_internal_identifier"), None
        ),
        created_by=admin_user.id,
        last_updated_by=admin_user.id,
    )
    if force_id and data.get("id"):
        officer.id = data["id"]
    db.session.add(officer)
    db.session.flush()

    return officer


def update_officer_from_dict(data: Dict[str, Any], officer: Officer) -> Officer:
    if "department_id" in data.keys():
        officer.department_id = int(data["department_id"])
    if "last_name" in data.keys():
        officer.last_name = parse_str(data.get("last_name", ""))
    if "first_name" in data.keys():
        officer.first_name = parse_str(data.get("first_name", ""))
    if "middle_initial" in data.keys():
        officer.middle_initial = parse_str(data.get("middle_initial", ""))
    if "suffix" in data.keys():
        officer.suffix = validate_choice(data.get("suffix", ""), SUFFIX_CHOICES)
    if "race" in data.keys():
        officer.race = validate_choice(data.get("race"), RACE_CHOICES)
    if "gender" in data.keys():
        officer.gender = validate_choice(data.get("gender"), GENDER_CHOICES)
    if "employment_date" in data.keys():
        officer.employment_date = parse_date(data.get("employment_date"))
    if "birth_year" in data.keys():
        officer.birth_year = parse_int(data.get("birth_year"))
    if "unique_internal_identifier" in data.keys():
        officer.unique_internal_identifier = parse_str(
            data.get("unique_internal_identifier"), None
        )
    officer.last_updated_by = User.query.filter_by(is_administrator=True).first().id
    db.session.flush()
    return officer


def create_assignment_from_dict(
    data: Dict[str, Any], force_id: bool = False
) -> Assignment:
    admin_user = User.query.filter_by(is_administrator=True).first()

    assignment = Assignment(
        officer_id=int(data["officer_id"]),
        star_no=parse_str(data.get("star_no"), None),
        job_id=int(data["job_id"]),
        unit_id=parse_int(data.get("unit_id")),
        start_date=parse_date(data.get("start_date")),
        resign_date=parse_date(data.get("resign_date")),
        created_by=admin_user.id,
        last_updated_by=admin_user.id,
    )
    if force_id and data.get("id"):
        assignment.id = data["id"]
    db.session.add(assignment)

    return assignment


def update_assignment_from_dict(
    data: Dict[str, Any], assignment: Assignment
) -> Assignment:
    if "officer_id" in data.keys():
        assignment.officer_id = int(data["officer_id"])
    if "star_no" in data.keys():
        assignment.star_no = parse_str(data.get("star_no"), None)
    if "job_id" in data.keys():
        assignment.job_id = int(data["job_id"])
    if "unit_id" in data.keys():
        assignment.unit_id = parse_int(data.get("unit_id"))
    if "start_date" in data.keys():
        assignment.start_date = parse_date(data.get("start_date"))
    if "resign_date" in data.keys():
        assignment.resign_date = parse_date(data.get("resign_date"))
    assignment.last_updated_by = User.query.filter_by(is_administrator=True).first().id
    db.session.flush()

    return assignment


def create_salary_from_dict(data: Dict[str, Any], force_id: bool = False) -> Salary:
    admin_user = User.query.filter_by(is_administrator=True).first()

    salary = Salary(
        officer_id=int(data["officer_id"]),
        salary=float(data["salary"]),
        overtime_pay=parse_float(data.get("overtime_pay")),
        year=int(data["year"]),
        is_fiscal_year=parse_bool(data.get("is_fiscal_year")),
        created_by=admin_user.id,
        last_updated_by=admin_user.id,
    )
    if force_id and data.get("id"):
        salary.id = data["id"]
    db.session.add(salary)

    return salary


def update_salary_from_dict(data: Dict[str, Any], salary: Salary) -> Salary:
    if "officer_id" in data.keys():
        salary.officer_id = int(data["officer_id"])
    if "salary" in data.keys():
        salary.salary = int(data["salary"])
    if "overtime_pay" in data.keys():
        salary.overtime_pay = parse_int(data.get("overtime_pay"))
    if "year" in data.keys():
        salary.year = int(data["year"])
    if "is_fiscal_year" in data.keys():
        salary.is_fiscal_year = parse_bool(data.get("is_fiscal_year"))
    salary.last_updated_by = User.query.filter_by(is_administrator=True).first().id
    db.session.flush()

    return salary


def create_link_from_dict(data: Dict[str, Any], force_id: bool = False) -> Link:
    admin_user = User.query.filter_by(is_administrator=True).first()

    link = Link(
        title=data.get("title", ""),
        url=url_validator(data["url"]),
        link_type=validate_choice(data.get("link_type"), LINK_CHOICES),
        description=parse_str(data.get("description"), None),
        author=parse_str(data.get("author"), None),
        created_by=parse_int(data.get("created_by", admin_user.id)),
        last_updated_by=parse_int(data.get("created_by", admin_user.id)),
    )

    if force_id and data.get("id"):
        link.id = data["id"]

    db.session.add(link)
    link.officers = data.get("officers") or []
    link.incidents = data.get("incidents") or []
    db.session.flush()

    return link


def update_link_from_dict(data: Dict[str, Any], link: Link) -> Link:
    if "title" in data:
        link.title = data.get("title", "")
    if "url" in data:
        link.url = url_validator(data["url"])
    if "link_type" in data:
        link.link_type = validate_choice(data.get("link_type"), LINK_CHOICES)
    if "description" in data:
        link.description = parse_str(data.get("description"), None)
    if "author" in data:
        link.author = parse_str(data.get("author"), None)
    if "officers" in data:
        link.officers = data.get("officers") or []
    if "incidents" in data:
        link.incidents = data.get("incidents") or []
    link.last_updated_by = User.query.filter_by(is_administrator=True).first().id
    db.session.flush()

    return link


def get_or_create_license_plate_from_dict(
    data: Dict[str, Any]
) -> Tuple[LicensePlate, bool]:
    number = data["number"]
    state = parse_str(data.get("state"), None)
    state_validator(state)
    return get_or_create(
        db.session,
        LicensePlate,
        number=number,
        state=state,
    )


def get_or_create_location_from_dict(
    data: Dict[str, Any]
) -> Tuple[Optional[Location], bool]:
    street_name = parse_str(data.get("street_name"), None)
    cross_street1 = parse_str(data.get("cross_street1"), None)
    cross_street2 = parse_str(data.get("cross_street2"), None)
    city = parse_str(data.get("city"), None)
    state = parse_str(data.get("state"), None)
    state_validator(state)
    zip_code = parse_str(data.get("zip_code"), None)

    if not any([street_name, cross_street1, cross_street2, city, state, zip_code]):
        return None, False

    return get_or_create(
        db.session,
        Location,
        street_name=street_name,
        cross_street1=cross_street1,
        cross_street2=cross_street2,
        city=city,
        state=state,
        zip_code=zip_code,
    )


def create_incident_from_dict(data: Dict[str, Any], force_id: bool = False) -> Incident:
    admin_user = User.query.filter_by(is_administrator=True).first()

    incident = Incident(
        date=parse_date(data.get("date")),
        time=parse_time(data.get("time")),
        report_number=parse_str(data.get("report_number"), None),
        description=parse_str(data.get("description"), None),
        address_id=data.get("address_id"),
        department_id=parse_int(data.get("department_id")),
        created_by=parse_int(data.get("created_by", admin_user.id)),
        last_updated_by=parse_int(data.get("last_updated_by", admin_user.id)),
    )

    incident.officers = data.get("officers", [])
    incident.license_plates = data.get("license_plate_objects", [])

    if force_id and data.get("id"):
        incident.id = data["id"]

    db.session.add(incident)

    return incident


def update_incident_from_dict(data: Dict[str, Any], incident: Incident) -> Incident:
    if "date" in data:
        incident.date = parse_date(data.get("date"))
    if "time" in data:
        incident.time = parse_time(data.get("time"))
    if "report_number" in data:
        incident.report_number = parse_str(data.get("report_number"), None)
    if "description" in data:
        incident.description = parse_str(data.get("description"), None)
    if "address_id" in data:
        incident.address_id = data.get("address_id")
    if "department_id" in data:
        incident.department_id = parse_int(
            data.get(
                "department_id", User.query.filter_by(is_administrator=True).first().id
            )
        )
    if "last_updated_by" in data:
        incident.last_updated_by = parse_int(
            data.get(
                "last_updated_by", User.query.filter_by(is_administrator=True).first()
            ),
        )
    if "officers" in data:
        incident.officers = data["officers"] or []
    if "license_plate_objects" in data:
        incident.license_plates = data["license_plate_objects"] or []
    db.session.flush()
    return incident


@login_manager.user_loader
def load_user(token):
    # Identify user using alternative token so their sessions are
    # automatically invalidated when they update their email or password.
    # https://flask-login.readthedocs.io/en/latest/#alternative-tokens
    return User.query.filter_by(_uuid=token).one_or_none()
