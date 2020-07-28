from __future__ import print_function
from builtins import input
from getpass import getpass
import sys
import csv
from datetime import datetime

import click
from flask.cli import with_appcontext
from flask import current_app

from .models import db, Assignment, Department, Officer, User, Salary, Job, Link, Incident
from .utils import get_officer, str_is_true

from OpenOversight.app.model_imports import (
    create_officer_from_dict, update_officer_from_dict,
    create_assignment_from_dict, update_assignment_from_dict,
    create_salary_from_dict, update_salary_from_dict,
    create_link_from_dict, update_link_from_dict,
    create_incident_from_dict, update_incident_from_dict,
    get_or_create_license_plate_from_dict, get_or_create_location_from_dict
)


@click.command()
@with_appcontext
def make_admin_user():
    "Add confirmed administrator account"
    while True:
        username = input("Username: ")
        user = User.query.filter_by(username=username).one_or_none()
        if user:
            print("Username is already in use")
        else:
            break

    while True:
        email = input("Email: ")
        user = User.query.filter_by(email=email).one_or_none()
        if user:
            print("Email address already in use")
        else:
            break

    while True:
        password = getpass("Password: ")
        password_again = getpass("Type your password again: ")

        if password == password_again:
            break
        print("Passwords did not match")

    u = User(username=username, email=email, password=password,
             confirmed=True, is_administrator=True)
    db.session.add(u)
    db.session.commit()
    print("Administrator {} successfully added".format(username))
    current_app.logger.info('Administrator {} added with email {}'.format(username,
                                                                          email))


@click.command()
@with_appcontext
def link_images_to_department():
    """Link existing images to first department"""
    from app.models import Image, db
    images = Image.query.all()
    print("Linking images to first department:")
    for image in images:
        if not image.department_id:
            sys.stdout.write(".")
            image.department_id = 1
        else:
            print("Skipped! Department already assigned")
    db.session.commit()


@click.command()
@with_appcontext
def link_officers_to_department():
    """Links officers and unit_ids to first department"""
    from app.models import Officer, Unit, db

    officers = Officer.query.all()
    units = Unit.query.all()

    print("Linking officers and units to first department:")
    for item in officers + units:
        if not item.department_id:
            sys.stdout.write(".")
            item.department_id = 1
        else:
            print("Skipped! Object already assigned to department!")
    db.session.commit()


class ImportLog:
    updated_officers = {}
    created_officers = {}

    @classmethod
    def log_change(cls, officer, msg):
        if officer.id not in cls.created_officers:
            if officer.id not in cls.updated_officers:
                cls.updated_officers[officer.id] = []
            log = cls.updated_officers[officer.id]
        else:
            log = cls.created_officers[officer.id]
        log.append(msg)

    @classmethod
    def log_new_officer(cls, officer):
        cls.created_officers[officer.id] = []

    @classmethod
    def print_create_logs(cls):
        officers = Officer.query.filter(
            Officer.id.in_(cls.created_officers.keys())).all()
        for officer in officers:
            print('Created officer {}'.format(officer))
            for msg in cls.created_officers[officer.id]:
                print(' --->', msg)

    @classmethod
    def print_update_logs(cls):
        officers = Officer.query.filter(
            Officer.id.in_(cls.updated_officers.keys())).all()
        for officer in officers:
            print('Updates to officer {}:'.format(officer))
            for msg in cls.updated_officers[officer.id]:
                print(' --->', msg)

    @classmethod
    def print_logs(cls):
        cls.print_create_logs()
        cls.print_update_logs()

    @classmethod
    def clear_logs(cls):
        cls.updated_officers = {}
        cls.created_officers = {}


def row_has_data(row, required_fields, optional_fields):
    for field in required_fields:
        if field not in row or not row[field]:
            return False
    n_optional = 0
    for field in optional_fields:
        if field in row and row[field]:
            n_optional += 1
    if len(required_fields) > 0 or n_optional > 0:
        return True
    return False


def set_field_from_row(row, obj, attribute, allow_blank=True, fieldname=None):
    fieldname = fieldname or attribute
    if fieldname in row and (row[fieldname] or allow_blank):
        try:
            val = datetime.strptime(row[fieldname], '%Y-%m-%d').date()
        except ValueError:
            val = row[fieldname]
        setattr(obj, attribute, val)


def update_officer_from_row(row, officer, update_static_fields=False):
    def update_officer_field(fieldname, allow_blank=True):
        if fieldname in row and (row[fieldname] or allow_blank) and \
                getattr(officer, fieldname) != row[fieldname]:
            ImportLog.log_change(
                officer,
                'Updated {}: {} --> {}'.format(
                    fieldname, getattr(officer, fieldname), row[fieldname]))
            setattr(officer, fieldname, row[fieldname])

    # Name and gender are the only potentially changeable fields, so update those
    update_officer_field('last_name', allow_blank=False)
    update_officer_field('first_name', allow_blank=False)
    update_officer_field('middle_initial')
    update_officer_field('suffix', allow_blank=False)
    update_officer_field('gender')

    # The rest should be static
    static_fields = [
        'unique_internal_identifier',
        'race',
        'employment_date',
        'birth_year'
    ]
    for fieldname in static_fields:
        if fieldname in row:
            if row[fieldname] == '':
                row[fieldname] = None
            old_value = getattr(officer, fieldname)
            new_value = row[fieldname]
            if old_value is None:
                update_officer_field(fieldname, new_value)
            elif str(old_value) != str(new_value):
                msg = 'Officer {} {} has differing {} field. Old: {}, new: {}'.format(
                    officer.first_name,
                    officer.last_name,
                    fieldname,
                    old_value,
                    new_value
                )
                if update_static_fields:
                    print(msg)
                    update_officer_field(fieldname, new_value)
                else:
                    raise Exception(msg)

    process_assignment(row, officer, compare=True)
    process_salary(row, officer, compare=True)


def create_officer_from_row(row, department_id):
    officer = Officer()
    officer.department_id = department_id

    set_field_from_row(row, officer, 'last_name', allow_blank=False)
    set_field_from_row(row, officer, 'first_name', allow_blank=False)
    set_field_from_row(row, officer, 'middle_initial')
    set_field_from_row(row, officer, 'suffix')
    set_field_from_row(row, officer, 'race')
    set_field_from_row(row, officer, 'gender')
    set_field_from_row(row, officer, 'employment_date', allow_blank=False)
    set_field_from_row(row, officer, 'birth_year')
    set_field_from_row(row, officer, 'unique_internal_identifier')
    db.session.add(officer)
    db.session.flush()

    ImportLog.log_new_officer(officer)

    process_assignment(row, officer, compare=False)
    process_salary(row, officer, compare=False)


def process_assignment(row, officer, compare=False):
    assignment_fields = {
        'required': ['job_title'],
        'optional': [
            'star_no',
            'unit_id',
            'star_date',
            'resign_date']
    }

    # See if the row has assignment data
    if row_has_data(row, assignment_fields['required'], assignment_fields['optional']):
        add_assignment = True
        if compare:
            # Get existing assignments for officer and compare to row data
            assignments = db.session.query(Assignment, Job)\
                            .filter(Assignment.job_id == Job.id)\
                            .filter_by(officer_id=officer.id)\
                            .all()
            for (assignment, job) in assignments:
                assignment_fieldnames = ['star_no', 'unit_id', 'star_date', 'resign_date']
                i = 0
                for fieldname in assignment_fieldnames:
                    current = getattr(assignment, fieldname)
                    # Test if fields match between row and existing assignment
                    if (current and fieldname in row and row[fieldname] == current) or \
                            (not current and (fieldname not in row or not row[fieldname])):
                        i += 1
                if i == len(assignment_fieldnames):
                    job_title = job.job_title
                    if (job_title and 'job_title' in row and row['job_title'] == job_title) or \
                            (not job_title and ('job_title' not in row or not row['job_title'])):
                        # Found match, so don't add new assignment
                        add_assignment = False
        if add_assignment:
            job = Job.query\
                     .filter_by(job_title=row['job_title'],
                                department_id=officer.department_id)\
                     .one_or_none()
            if not job:
                num_existing_ranks = len(Job.query.filter_by(department_id=officer.department_id).all())
                if num_existing_ranks > 0:
                    auto_order = num_existing_ranks + 1
                else:
                    auto_order = 0
                # create new job
                job = Job(
                    is_sworn_officer=False,
                    department_id=officer.department_id,
                    order=auto_order
                )
                set_field_from_row(row, job, 'job_title', allow_blank=False)
                db.session.add(job)
                db.session.flush()
            # create new assignment
            assignment = Assignment()
            assignment.officer_id = officer.id
            assignment.job_id = job.id
            set_field_from_row(row, assignment, 'star_no')
            set_field_from_row(row, assignment, 'unit_id')
            set_field_from_row(row, assignment, 'star_date', allow_blank=False)
            set_field_from_row(row, assignment, 'resign_date', allow_blank=False)
            db.session.add(assignment)
            db.session.flush()

            ImportLog.log_change(officer, 'Added assignment: {}'.format(assignment))


def process_salary(row, officer, compare=False):
    salary_fields = {
        'required': [
            'salary',
            'salary_year',
            'salary_is_fiscal_year'],
        'optional': ['overtime_pay']
    }

    # See if the row has salary data
    if row_has_data(row, salary_fields['required'], salary_fields['optional']):
        is_fiscal_year = str_is_true(row['salary_is_fiscal_year'])

        add_salary = True
        if compare:
            # Get existing salaries for officer and compare to row data
            salaries = Salary.query.filter_by(officer_id=officer.id).all()
            for salary in salaries:
                from decimal import Decimal
                print(vars(salary))
                print(row)
                if Decimal('%.2f' % salary.salary) == Decimal('%.2f' % float(row['salary'])) and \
                        salary.year == int(row['salary_year']) and \
                        salary.is_fiscal_year == is_fiscal_year and \
                        ((salary.overtime_pay and 'overtime_pay' in row and
                            Decimal('%.2f' % salary.overtime_pay) == Decimal('%.2f' % float(row['overtime_pay']))) or
                            (not salary.overtime_pay and ('overtime_pay' not in row or not row['overtime_pay']))):
                    # Found match, so don't add new salary
                    add_salary = False

        if add_salary:
            # create new salary
            salary = Salary(
                officer_id=officer.id,
                salary=float(row['salary']),
                year=int(row['salary_year']),
                is_fiscal_year=is_fiscal_year,
            )
            if 'overtime_pay' in row and row['overtime_pay']:
                salary.overtime_pay = float(row['overtime_pay'])
            db.session.add(salary)
            db.session.flush()

            ImportLog.log_change(officer, 'Added salary: {}'.format(salary))


@click.command()
@click.argument('filename')
@click.option('--no-create', is_flag=True, help='only update officers; do not create new ones')
@click.option('--update-by-name', is_flag=True, help='update officers by first and last name (useful when star_no or unique_internal_identifier are not available)')
@click.option('--update-static-fields', is_flag=True, help='allow updating normally-static fields like race, birth year, etc.')
@with_appcontext
def bulk_add_officers(filename, no_create, update_by_name, update_static_fields):
    """Add or update officers from a CSV file."""
    with open(filename, 'r') as f:
        ImportLog.clear_logs()
        csvfile = csv.DictReader(f)
        departments = {}

        required_fields = [
            'department_id',
            'first_name',
            'last_name',
        ]

        # Assert required fields are in CSV file
        for field in required_fields:
            if field not in csvfile.fieldnames:
                raise Exception('Missing required field {}'.format(field))
        if (not update_by_name
                and 'star_no' not in csvfile.fieldnames
                and 'unique_internal_identifier' not in csvfile.fieldnames):
            raise Exception('CSV file must include either badge numbers or unique identifiers for officers')

        for row in csvfile:
            department_id = row['department_id']
            department = departments.get(department_id)
            if row['department_id'] not in departments:
                department = Department.query.filter_by(id=department_id).one_or_none()
                if department:
                    departments[department_id] = department
                else:
                    raise Exception('Department ID {} not found'.format(department_id))

            if not update_by_name:
                # check for existing officer based on unique ID or name/badge
                if 'unique_internal_identifier' in csvfile.fieldnames and row['unique_internal_identifier']:
                    officer = Officer.query.filter_by(
                        department_id=department_id,
                        unique_internal_identifier=row['unique_internal_identifier']
                    ).one_or_none()
                elif 'star_no' in csvfile.fieldnames and row['star_no']:
                    officer = get_officer(department_id, row['star_no'],
                                          row['first_name'], row['last_name'])
                else:
                    raise Exception('Officer {} {} missing badge number and unique identifier'.format(row['first_name'],
                                                                                                      row['last_name']))
            else:
                officer = Officer.query.filter_by(
                    department_id=department_id,
                    last_name=row['last_name'],
                    first_name=row['first_name']
                ).one_or_none()

            if officer:
                update_officer_from_row(row, officer, update_static_fields)
            elif not no_create:
                create_officer_from_row(row, department_id)

        db.session.commit()

        ImportLog.print_logs()

        return len(ImportLog.created_officers), len(ImportLog.updated_officers)


def _create_or_update_model(
    row, existing_model_lookup, create_method, update_method, force_create
):
    if not row["id"]:
        return create_method(row)
    else:
        if not force_create:
            return update_method(row, existing_model_lookup[int(row["id"])])
        else:
            model = existing_model_lookup.get(int(row["id"]))
            if model:
                db.session.delete(model)
                db.session.flush()
            return create_method(row, force_id=True)


def _check_provided_fields(dict_reader, required_fields, optional_fields, csv_name):
    missing_required = set(required_fields) - set(dict_reader.fieldnames)
    if len(missing_required)>0:
        raise Exception(
                "Missing mandatory field(s) {} in {} csv."
                .format(list(missing_required), csv_name)
            )
    unexpected_fields = set(dict_reader.fieldnames) - set(required_fields + optional_fields) 
    if len(unexpected_fields)>0:
        raise Exception(
                "Received unexpected field(s) {} in {} csv."
                .format(list(unexpected_fields), csv_name)
            )


def _objects_from_split_field(field, model_lookup):
    if field:
        return [model_lookup[object_id] for object_id in field.split("|")]
    return []


@click.command()
@click.argument("department-name")
@click.option("--officers-csv")
@click.option("--assignments-csv")
@click.option("--salaries-csv")
@click.option("--links-csv")
@click.option("--incidents-csv")
@click.option("--force-create", is_flag=True, help="Only for development/testing!")
@with_appcontext
def load_csv_into_database(
    department_name,
    officers_csv,
    assignments_csv,
    salaries_csv,
    links_csv,
    incidents_csv,
    force_create,
):
    """Add or update officers from a CSV file.
    The CSV file is treated as the sole source of truth!!"""
    if force_create and current_app.config["ENV"] == "production":
        raise Exception("--force-create cannot be used in production!")
    department_id = Department.query.filter_by(name=department_name).one().id

    new_officers = {}
    existing_officers = Officer.query.filter_by(department_id=department_id).all()
    id_to_officer = {officer.id: officer for officer in existing_officers}

    counter = 0
    if officers_csv is not None:
        with open(officers_csv) as f:
            csv_reader = csv.DictReader(f)
            field_names = [
                field_name.replace(" ", "_") for field_name in csv_reader.fieldnames
            ]
            csv_reader.fieldnames = field_names
            _check_provided_fields(
                csv_reader, 
                required_fields=["id", "department_id"],
                optional_fields=["last_name", "first_name", "middle_initial",
                "suffix", "race", "gender", "employment_date", "birth_year",
                "unique_internal_identifier",
                # the following are unused, but allowed since they are included in the csv output
                "badge_number", "job_title", "most_recent_salary"
                ],
                csv_name="officers"
            )

            for row in csv_reader:
                 # can only update department with given name
                assert department_id == int(row["department_id"])
                connection_id = None
                if row["id"].startswith("#"):
                    connection_id = row["id"]
                    row["id"] = ""
                officer = _create_or_update_model(
                    row=row,
                    existing_model_lookup=id_to_officer,
                    create_method=create_officer_from_dict,
                    update_method=update_officer_from_dict,
                    force_create=force_create,
                )
                if connection_id is not None:
                    new_officers[connection_id] = officer
                counter += 1
                if counter % 100 == 0:
                    print("Processed {} officers.".format(counter))
        print("Done with officers. Processed {} rows.".format(counter))

    all_officers = {str(k): v for k, v in id_to_officer.items()}
    all_officers.update(new_officers)

    counter = 0
    if assignments_csv is not None:
        with open(assignments_csv) as f:
            csv_reader = csv.DictReader(f)
            field_names = [
                field_name.replace(" ", "_") for field_name in csv_reader.fieldnames
            ]
            if "start_date" in field_names:
                field_names[field_names.index("start_date")] = "star_date"
            if "badge_number" in field_names:
                field_names[field_names.index("badge_number")] = "star_no"
            csv_reader.fieldnames = field_names
            _check_provided_fields(
                csv_reader, 
                required_fields=["id", "officer_id", "job_title"],
                optional_fields=["star_no", "unit_id", "star_date", "resign_date"],
                csv_name="assignments"
            )
            jobs_for_department = list(
                Job.query.filter_by(department_id=department_id).all()
            )
            job_title_to_id = {job.job_title: job.id for job in jobs_for_department}
            existing_assignments = (
                Assignment.query.join(Assignment.baseofficer)
                .filter(Officer.department_id == department_id)
                .all()
            )
            id_to_assignment = {
                assignment.id: assignment for assignment in existing_assignments
            }
            for row in csv_reader:
                job_id = job_title_to_id.get(row["job_title"])
                if job_id is None:
                    raise Exception(
                        "Job title {} not found for department.".format(
                            row["job_title"]
                        )
                    )
                row["job_id"] = job_id
                officer = all_officers.get(row["officer_id"])
                if not officer:
                    raise Exception("Officer with id {} does not exist (in this department)".format(row["officer_id"]))
                row["officer_id"] = officer.id
                _create_or_update_model(
                    row=row,
                    existing_model_lookup=id_to_assignment,
                    create_method=create_assignment_from_dict,
                    update_method=update_assignment_from_dict,
                    force_create=force_create,
                )
                counter += 1
                if counter % 100 == 0:
                    print("Processed {} assignments.".format(counter))
        print("Done with assignments. Processed {} rows.".format(counter))

    counter = 0
    if salaries_csv is not None:
        with open(salaries_csv) as f:
            csv_reader = csv.DictReader(f)
            field_names = [
                field_name.replace(" ", "_") for field_name in csv_reader.fieldnames
            ]
            csv_reader.fieldnames = field_names
            _check_provided_fields(
                csv_reader, 
                required_fields=["id", "officer_id", "salary", "year"],
                optional_fields=["overtime_pay", "is_fiscal_year"],
                csv_name="salaries"
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
                    raise Exception("Officer with id {} does not exist (in this department)".format(row["officer_id"]))
                row["officer_id"] = officer.id
                _create_or_update_model(
                    row=row,
                    existing_model_lookup=id_to_salary,
                    create_method=create_salary_from_dict,
                    update_method=update_salary_from_dict,
                    force_create=force_create,
                )
                counter += 1
                if counter % 100 == 0:
                    print("Processed {} salaries.".format(counter))
        print("Done with salaries. Processed {} rows.".format(counter))

    if incidents_csv is not None or links_csv is not None:
        existing_incidents = Incident.query.filter_by(department_id=department_id).all()
        id_to_incident = {incident.id: incident for incident in existing_incidents}
        all_incidents = {str(k): v for k, v in id_to_incident.items()}
    counter = 0
    if incidents_csv is not None:
        with open(incidents_csv) as f:
            csv_reader = csv.DictReader(f)
            field_names = [
                field_name.replace(" ", "_") for field_name in csv_reader.fieldnames
            ]
            csv_reader.fieldnames = field_names
            _check_provided_fields(
                csv_reader,
                required_fields=["id", "department_id"],
                optional_fields=["date", "time", "report_number", "description", "street_name", "cross_street1", "cross_street2", "city", "state", "zip_code", "creator_id", "last_updated_id", "officer_ids", "license_plates"],
                csv_name="incidents"
            )

            for row in csv_reader:
                assert int(row["department_id"]) == department_id
                row["officers"] = _objects_from_split_field(
                    row.get("officer_ids"), all_officers
                )
                address, _ = get_or_create_location_from_dict(row)
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
                connection_id = None
                if row["id"].startswith("#"):
                    connection_id = row["id"]
                    row["id"] = ""
                incident = _create_or_update_model(
                    row=row,
                    existing_model_lookup=id_to_incident,
                    create_method=create_incident_from_dict,
                    update_method=update_incident_from_dict,
                    force_create=force_create,
                )
                if connection_id:
                    all_incidents[connection_id] = incident
                counter += 1
                if counter % 100 == 0:
                    print("Processed {} incidents.".format(counter))
            print("Done with incidents. Processed {} rows.".format(counter))

    counter = 0
    if links_csv is not None:
        with open(links_csv) as f:
            csv_reader = csv.DictReader(f)
            field_names = [
                field_name.replace(" ", "_") for field_name in csv_reader.fieldnames
            ]
            csv_reader.fieldnames = field_names
            _check_provided_fields(
                csv_reader,
                required_fields=["id", "url"],
                optional_fields=["title", "link_type", "description", "author", "user_id", "officer_ids", "incident_ids"],
                csv_name="links"
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
                link.id: link
                for link in existing_officer_links + existing_incident_links
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
                )
                counter += 1
                if counter % 100 == 0:
                    print("Processed {} links.".format(counter))
            print("Done with links. Processed {} rows.".format(counter))

    db.session.commit()
    print("All committed.")


@click.command()
@click.argument('name')
@click.argument('short_name')
@click.argument('unique_internal_identifier', required=False)
@with_appcontext
def add_department(name, short_name, unique_internal_identifier):
    """Add a new department to OpenOversight."""
    dept = Department(name=name, short_name=short_name, unique_internal_identifier_label=unique_internal_identifier)
    db.session.add(dept)
    db.session.commit()
    print("Department added with id {}".format(dept.id))


@click.command()
@click.argument('department_id')
@click.argument('job_title')
@click.argument('is_sworn_officer', type=click.Choice(["true", "false"], case_sensitive=False))
@click.argument('order', type=int)
@with_appcontext
def add_job_title(department_id, job_title, is_sworn_officer, order):
    """Add a rank to a department."""
    department = Department.query.filter_by(id=department_id).one_or_none()
    is_sworn = (is_sworn_officer == "true")
    job = Job(job_title=job_title, is_sworn_officer=is_sworn, order=order, department=department)
    db.session.add(job)
    print('Added {} to {}'.format(job.job_title, department.name))
    db.session.commit()
