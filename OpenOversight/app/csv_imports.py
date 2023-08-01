import csv
from contextlib import contextmanager
from typing import Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from OpenOversight.app.models.database import (
    Assignment,
    Department,
    Incident,
    Job,
    Link,
    Officer,
    Salary,
    Unit,
    db,
)
from OpenOversight.app.models.database_imports import (
    create_assignment_from_dict,
    create_incident_from_dict,
    create_link_from_dict,
    create_officer_from_dict,
    create_salary_from_dict,
    get_or_create_license_plate_from_dict,
    get_or_create_location_from_dict,
    update_assignment_from_dict,
    update_incident_from_dict,
    update_link_from_dict,
    update_officer_from_dict,
    update_salary_from_dict,
)


def _create_or_update_model(
    row,
    existing_model_lookup,
    create_method,
    update_method,
    force_create=False,
    model=None,
    always_create=False,
):
    if (always_create and not force_create) or not row["id"]:
        return create_method(row)
    else:
        if not force_create:
            return update_method(row, existing_model_lookup[int(row["id"])])
        else:
            if model is not None:
                existing = model.query.filter_by(id=int(row["id"])).first()
                if existing:
                    db.session.delete(existing)
                    db.session.flush()
            return create_method(row, force_id=True)


def _check_provided_fields(dict_reader, required_fields, optional_fields, csv_name):
    missing_required = set(required_fields) - set(dict_reader.fieldnames)
    if len(missing_required) > 0:
        raise Exception(
            f"Missing mandatory field(s) {list(missing_required)} in {csv_name} csv."
        )
    unexpected_fields = set(dict_reader.fieldnames) - set(
        required_fields + optional_fields
    )
    if len(unexpected_fields) > 0:
        raise Exception(
            f"Received unexpected field(s) {list(unexpected_fields)} in {csv_name} csv."
        )


def _objects_from_split_field(field, model_lookup):
    if field:
        return [model_lookup[object_id] for object_id in field.split("|")]
    return []


def _unify_field_names(fieldnames):
    return [field_name.lower().replace(" ", "_") for field_name in fieldnames]


@contextmanager
def _csv_reader(csv_filename):
    with open(csv_filename) as f:
        csv_reader = csv.DictReader(f)
        csv_reader.fieldnames = _unify_field_names(csv_reader.fieldnames)
        yield csv_reader


def _handle_officers_csv(
    officers_csv: str,
    department_name: str,
    department_state: str,
    department_id: int,
    id_to_officer,
    force_create,
) -> Dict[str, Officer]:
    new_officers = {}
    counter = 0
    with _csv_reader(officers_csv) as csv_reader:
        _check_provided_fields(
            csv_reader,
            required_fields=["id", "department_name", "department_state"]
            if not force_create
            else ["id"],
            optional_fields=[
                "last_name",
                "first_name",
                "middle_initial",
                "suffix",
                "race",
                "gender",
                "employment_date",
                "birth_year",
                "unique_internal_identifier",
                "department_name",
                "department_state",
                # the following are unused, but allowed since they are included in the
                # csv output
                "badge_number",
                "unique_identifier",
                "job_title",
                "most_recent_salary",
                "last_employment_date",
                "last_employment_notice",
            ],
            csv_name="officers",
        )

        for row in csv_reader:
            # can only update department with given name
            if not force_create:
                assert row["department_name"] == department_name
                assert row["department_state"] == department_state
            row["department_id"] = department_id
            connection_id = row["id"]
            if row["id"].startswith("#"):
                row["id"] = ""
            officer = _create_or_update_model(
                row=row,
                existing_model_lookup=id_to_officer,
                create_method=create_officer_from_dict,
                update_method=update_officer_from_dict,
                force_create=force_create,
                model=Officer,
            )
            if connection_id is not None:
                new_officers[connection_id] = officer
            counter += 1
            if counter % 1000 == 0:
                print(f"Processed {counter} officers.")
    print(f"Done with officers. Processed {counter} rows.")
    return new_officers


def _handle_assignments_csv(
    assignments_csv: str,
    department_id: int,
    all_officers: Dict[str, Officer],
    force_create: bool,
    overwrite_assignments: bool,
) -> None:
    counter = 0
    with _csv_reader(assignments_csv) as csv_reader:
        field_names = csv_reader.fieldnames
        if "start_date" in field_names:
            field_names[field_names.index("start_date")] = "start_date"
        if "badge_number" in field_names:
            field_names[field_names.index("badge_number")] = "star_no"
        if "end_date" in field_names:
            field_names[field_names.index("end_date")] = "resign_date"
        if "unit_description" in field_names:
            field_names[field_names.index("unit_description")] = "unit_name"
        required_fields = ["officer_id", "job_title"]
        if not overwrite_assignments:
            required_fields.append("id")

        _check_provided_fields(
            csv_reader,
            required_fields=required_fields,
            optional_fields=[
                "id",
                "star_no",
                "unit_id",
                "unit_name",
                "start_date",
                "resign_date",
                "officer_unique_identifier",
            ],
            csv_name="assignments",
        )
        jobs_for_department = list(
            Job.query.filter_by(department_id=department_id).all()
        )
        job_title_to_id = {
            job.job_title.strip().lower(): job.id for job in jobs_for_department
        }
        unit_description_to_id = {
            unit.description.strip().lower(): unit.id
            for unit in Unit.query.filter_by(department_id=department_id).all()
        }
        if overwrite_assignments:
            id_to_assignment = {}
            rows = []
            all_rel_officers = set()
            for row in csv_reader:
                rows.append(row)
                officer_id = row["officer_id"]
                if officer_id != "" and officer_id[0] != "#":
                    all_rel_officers.add(int(officer_id))
            wrong_department = all_rel_officers - set(
                [int(oid) for oid in all_officers.keys() if oid[0] != "#"]
            )
            if len(wrong_department) > 0:
                raise Exception(
                    "Referenced {} officers in assignment csv that belong to different "
                    "department. Example ids: {}".format(
                        len(wrong_department),
                        ", ".join(map(str, list(wrong_department)[:3])),
                    )
                )
            print(
                "Deleting assignments from {} officers to overwrite.".format(
                    len(all_rel_officers)
                )
            )
            (
                db.session.query(Assignment)
                .filter(Assignment.officer_id.in_(all_rel_officers))
                .delete(synchronize_session=False)
            )
            db.session.flush()
            # assign rows to csv_reader since we already iterated over reader
            csv_reader = rows
        else:
            existing_assignments = (
                Assignment.query.join(Assignment.base_officer)
                .filter(Officer.department_id == department_id)
                .all()
            )
            id_to_assignment = {
                assignment.id: assignment for assignment in existing_assignments
            }
        for row in csv_reader:
            officer = all_officers.get(row["officer_id"])
            if not officer:
                raise Exception(
                    "Officer with id {} does not exist (in this department)".format(
                        row["officer_id"]
                    )
                )
            if row.get("unit_id"):
                assert (
                    Unit.query.filter_by(id=int(row.get("unit_id"))).one().department.id
                    == department_id
                )
            elif row.get("unit_name"):
                unit_name = row["unit_name"].strip()
                description = unit_name.lower()
                unit_id = unit_description_to_id.get(description)
                if unit_id is None:
                    unit = Unit(
                        description=unit_name,
                        department_id=officer.department_id,
                    )
                    db.session.add(unit)
                    db.session.flush()
                    unit_id = unit.id
                    unit_description_to_id[description] = unit_id
                row["unit_id"] = unit_id
            job_title = row["job_title"].strip().lower()
            job_id = job_title_to_id.get(job_title)
            if job_id is None:
                num_existing_ranks = len(
                    Job.query.filter_by(department_id=officer.department_id).all()
                )
                if num_existing_ranks > 0:
                    auto_order = num_existing_ranks + 1
                else:
                    auto_order = 0
                # create new job
                job = Job(
                    job_title=row["job_title"].strip(),
                    is_sworn_officer=False,
                    department_id=officer.department_id,
                    order=auto_order,
                )
                db.session.add(job)
                db.session.flush()
                job_id = job.id
                job_title_to_id[job_title] = job_id

            row["job_id"] = job_id
            row["officer_id"] = officer.id
            _create_or_update_model(
                row=row,
                existing_model_lookup=id_to_assignment,
                create_method=create_assignment_from_dict,
                update_method=update_assignment_from_dict,
                force_create=force_create,
                model=Assignment,
                always_create=overwrite_assignments,
            )
            counter += 1
            if counter % 1000 == 0:
                print(f"Processed {counter} assignments.")
    print(f"Done with assignments. Processed {counter} rows.")


def _handle_salaries(
    salaries_csv: str,
    department_id: int,
    all_officers: Dict[str, Officer],
    force_create: bool,
) -> None:
    counter = 0
    with _csv_reader(salaries_csv) as csv_reader:
        _check_provided_fields(
            csv_reader,
            required_fields=["id", "officer_id", "salary", "year"],
            optional_fields=["overtime_pay", "is_fiscal_year"],
            csv_name="salaries",
        )
        existing_salaries = (
            Salary.query.join(Salary.officer)
            .filter(Officer.department_id == department_id)
            .all()
        )
        id_to_salary = {salary.id: salary for salary in existing_salaries}
        for row in csv_reader:
            officer = all_officers.get(row["officer_id"])
            if not officer:
                raise Exception(
                    "Officer with id {} does not exist (in this department)".format(
                        row["officer_id"]
                    )
                )
            row["officer_id"] = officer.id
            _create_or_update_model(
                row=row,
                existing_model_lookup=id_to_salary,
                create_method=create_salary_from_dict,
                update_method=update_salary_from_dict,
                force_create=force_create,
                model=Salary,
            )
            counter += 1
            if counter % 1000 == 0:
                print(f"Processed {counter} salaries.")
    print(f"Done with salaries. Processed {counter} rows.")


def _handle_incidents_csv(
    incidents_csv: str,
    department_name: str,
    department_state: str,
    department_id: int,
    all_officers: Dict[str, Officer],
    id_to_incident: Dict[int, Incident],
    force_create: bool,
) -> Dict[str, Incident]:
    counter = 0
    new_incidents = {}
    with _csv_reader(incidents_csv) as csv_reader:
        _check_provided_fields(
            csv_reader,
            required_fields=["id", "department_name", "department_state"],
            optional_fields=[
                "date",
                "time",
                "report_number",
                "description",
                "street_name",
                "cross_street1",
                "cross_street2",
                "city",
                "state",
                "zip_code",
                "created_by",
                "last_updated_by",
                "officer_ids",
                "license_plates",
            ],
            csv_name="incidents",
        )

        for row in csv_reader:
            assert row["department_name"] == department_name
            assert row["department_state"] == department_state
            row["department_id"] = department_id
            row["officers"] = _objects_from_split_field(
                row.get("officer_ids"), all_officers
            )
            address, _ = get_or_create_location_from_dict(row)
            if address is not None:
                row["address_id"] = address.id
            license_plates = []
            for license_plate_str in row.get("license_plates", "").split("|"):
                if license_plate_str:
                    parts = license_plate_str.split("_")
                    data = dict(zip(["number", "state"], parts))
                    license_plate, _ = get_or_create_license_plate_from_dict(data)
                    license_plates.append(license_plate)
            db.session.flush()

            if license_plates:
                row["license_plate_objects"] = license_plates
            connection_id = row["id"]
            if row["id"].startswith("#"):
                row["id"] = ""
            incident = _create_or_update_model(
                row=row,
                existing_model_lookup=id_to_incident,
                create_method=create_incident_from_dict,
                update_method=update_incident_from_dict,
                force_create=force_create,
                model=Incident,
            )
            if connection_id:
                new_incidents[connection_id] = incident
            counter += 1
            if counter % 1000 == 0:
                print(f"Processed {counter} incidents.")
        print(f"Done with incidents. Processed {counter} rows.")
    return new_incidents


def _handle_links_csv(
    links_csv: str,
    department_id: int,
    all_officers: Dict[str, Officer],
    all_incidents: Dict[str, Incident],
    force_create: bool,
) -> None:
    counter = 0
    with _csv_reader(links_csv) as csv_reader:
        _check_provided_fields(
            csv_reader,
            required_fields=["id", "url"],
            optional_fields=[
                "title",
                "link_type",
                "description",
                "author",
                "created_by",
                "officer_ids",
                "incident_ids",
            ],
            csv_name="links",
        )
        existing_officer_links = (
            Link.query.join(Link.officers)
            .filter(Officer.department_id == department_id)
            .all()
        )
        existing_incident_links = (
            Link.query.join(Link.incidents)
            .filter(Incident.department_id == department_id)
            .all()
        )
        id_to_link = {
            link.id: link for link in existing_officer_links + existing_incident_links
        }
        for row in csv_reader:
            row["officers"] = _objects_from_split_field(
                row.get("officer_ids"), all_officers
            )
            row["incidents"] = _objects_from_split_field(
                row.get("incident_ids"), all_incidents
            )
            _create_or_update_model(
                row=row,
                existing_model_lookup=id_to_link,
                create_method=create_link_from_dict,
                update_method=update_link_from_dict,
                force_create=force_create,
                model=Link,
            )
            counter += 1
            if counter % 1000 == 0:
                print(f"Processed {counter} links.")
        print(f"Done with links. Processed {counter} rows.")


def import_csv_files(
    department_name: str,
    department_state: str,
    officers_csv: Optional[str],
    assignments_csv: Optional[str],
    salaries_csv: Optional[str],
    links_csv: Optional[str],
    incidents_csv: Optional[str],
    force_create: bool = False,
    overwrite_assignments: bool = False,
):
    department = Department.query.filter_by(
        name=department_name, state=department_state
    ).one_or_none()
    if department is None:
        raise Exception(
            f"Department with name '{department_name}' in {department_state} "
            "does not exist!"
        )
    department_id = department.id

    existing_officers = Officer.query.filter_by(department_id=department_id).all()
    id_to_officer = {officer.id: officer for officer in existing_officers}
    all_officers = {str(k): v for k, v in id_to_officer.items()}

    if officers_csv is not None:
        new_officers = _handle_officers_csv(
            officers_csv,
            department_name,
            department_state,
            department_id,
            id_to_officer,
            force_create,
        )
        all_officers.update(new_officers)

    if assignments_csv is not None:
        _handle_assignments_csv(
            assignments_csv,
            department_id,
            all_officers,
            force_create,
            overwrite_assignments,
        )

    if salaries_csv is not None:
        _handle_salaries(salaries_csv, department_id, all_officers, force_create)

    if incidents_csv is not None or links_csv is not None:
        existing_incidents = Incident.query.filter_by(department_id=department_id).all()
        id_to_incident = {incident.id: incident for incident in existing_incidents}
        all_incidents = {str(k): v for k, v in id_to_incident.items()}

    if incidents_csv is not None:
        new_incidents = _handle_incidents_csv(
            incidents_csv,
            department_name,
            department_state,
            department_id,
            all_officers,
            id_to_incident,
            force_create,
        )
        all_incidents.update(new_incidents)

    if links_csv is not None:
        _handle_links_csv(
            links_csv, department_id, all_officers, all_incidents, force_create
        )

    db.session.commit()
    print("All committed.")

    if force_create:
        # This will only work in postgres and fail in sqlite
        raw_sql = """
        select setval('officers_id_seq', (select max(id) from officers));
        select setval('salaries_id_seq', (select max(id) from salaries));
        select setval('assignments_id_seq', (select max(id) from assignments));
        select setval('links_id_seq', (select max(id) from links));
        select setval('incidents_id_seq', (select max(id) from incidents));
        """
        try:
            db.session.execute(raw_sql)
            print("Updated sequences.")
        except SQLAlchemyError:
            print("Failed to update sequences")
