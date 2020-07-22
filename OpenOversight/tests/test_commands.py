import csv
import traceback
import uuid

from sqlalchemy.orm.exc import MultipleResultsFound

import pandas as pd
import pytest
from click.testing import CliRunner
from OpenOversight.app.commands import add_department, add_job_title, bulk_add_officers
from OpenOversight.app.models import Assignment, Department, Job, Officer, Salary
from OpenOversight.app.utils import get_officer
from OpenOversight.tests.conftest import RANK_CHOICES_1, generate_officer


def run_command_print_output(cli, args=None, **kwargs):
    """
    This function runs the given command with the provided arguments
    and returns a `result` object. The most relevant part of that object is
    the exit_code, were 0 indicates a successful run of the command and
    any other value signifies a failure.

    Additionally this function will send all generated logs to stdout
    and will print exceptions and strack-trace to make it easier to debug
    a failing
    """
    runner = CliRunner()
    result = runner.invoke(cli, args=args, **kwargs)
    print(result.output)
    print(result.stderr_bytes)
    if result.exception is not None:
        print(result.exception)
        print(traceback.print_exception(*result.exc_info))
    return result


def test_add_department__success(session):
    name = "Added Police Department"
    short_name = "APD"
    unique_internal_identifier = "30ad0au239eas939asdj"

    # add department via command line
    result = run_command_print_output(
        add_department, [name, short_name, unique_internal_identifier]
    )

    # command ran successful
    assert result.exit_code == 0
    # department was added to database
    departments = Department.query.filter_by(
        unique_internal_identifier_label=unique_internal_identifier
    ).all()
    assert len(departments) == 1
    department = departments[0]
    assert department.name == name
    assert department.short_name == short_name


def test_add_department__duplicate(session):
    name = "Duplicate Department"
    short_name = "DPD"
    department = Department(name=name, short_name=short_name)
    session.add(department)
    session.commit()

    # adding department of same name via command
    result = run_command_print_output(
        add_department, [name, short_name, "2320wea0s9d03eas"]
    )

    # fails because Department with this name already exists
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_department__missing_argument(session):
    # running add-department command missing one argument
    result = run_command_print_output(add_department, ["Name of Department"])

    # fails because short name is required argument
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_job_title__success(session, department):
    department_id = department.id

    job_title = "Police Officer"
    is_sworn = True
    order = 1

    # run command to add job title
    result = run_command_print_output(
        add_job_title, [str(department_id), job_title, str(is_sworn), str(order)]
    )

    assert result.exit_code == 0

    # confirm that job title was added to database
    jobs = Job.query.filter_by(department_id=department_id, job_title=job_title).all()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_title == job_title
    assert job.is_sworn_officer == is_sworn
    assert job.order == order


def test_add_job_title__duplicate(session, department):
    job_title = "Police Officer"
    is_sworn = True
    order = 1
    job = Job(
        job_title=job_title,
        is_sworn_officer=is_sworn,
        order=order,
        department=department,
    )
    session.add(job)
    session.commit()

    # adding exact same job again via command
    result = run_command_print_output(
        add_department, [str(department.id), job_title, str(is_sworn), str(order)]
    )

    # fails because this job already exists
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_job_title__different_departments(session, department):
    other_department = Department(name="Other Police Department", short_name="OPD")
    session.add(other_department)
    session.commit()
    other_department_id = other_department.id

    job_title = "Police Officer"
    is_sworn = True
    order = 1
    job = Job(
        job_title=job_title,
        is_sworn_officer=is_sworn,
        order=order,
        department=department,
    )
    session.add(job)
    session.commit()

    # adding samme job but for different department
    result = run_command_print_output(
        add_job_title, [str(other_department_id), job_title, str(is_sworn), str(order)]
    )

    # success because this department doesn't have that title yet
    assert result.exit_code == 0

    jobs = Job.query.filter_by(
        department_id=other_department_id, job_title=job_title
    ).all()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_title == job_title
    assert job.is_sworn_officer == is_sworn
    assert job.order == order


def test_csv_import_new(csvfile):
    # Delete all current officers
    Officer.query.delete()

    assert Officer.query.count() == 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created > 0
    assert Officer.query.count() == n_created
    assert n_updated == 0


def test_csv_import_update(csvfile):
    n_existing = Officer.query.count()

    assert n_existing > 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created == 0
    assert n_updated == 0
    assert Officer.query.count() == n_existing


def test_csv_import_idempotence(csvfile):
    # Delete all current officers
    Officer.query.delete()

    assert Officer.query.count() == 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created > 0
    assert n_updated == 0
    officer_count = Officer.query.count()
    assert officer_count == n_created

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated == 0
    assert Officer.query.count() == officer_count


def test_csv_missing_required_field(csvfile):
    df = pd.read_csv(csvfile)
    df.drop(columns="first_name").to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert "Missing required field" in str(exc.value)


def test_csv_missing_badge_and_uid(csvfile):
    df = pd.read_csv(csvfile)
    df.drop(columns=["star_no", "unique_internal_identifier"]).to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert (
        "CSV file must include either badge numbers or unique identifiers for officers"
        in str(exc.value)
    )


def test_csv_non_existant_dept_id(csvfile):
    df = pd.read_csv(csvfile)
    df["department_id"] = 666
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert "Department ID 666 not found" in str(exc.value)


def test_csv_officer_missing_badge_and_uid(csvfile):
    df = pd.read_csv(csvfile)
    df.loc[0, "star_no"] = None
    df.loc[0, "unique_internal_identifier"] = None
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert "missing badge number and unique identifier" in str(exc.value)


def test_csv_changed_static_field(csvfile):
    df = pd.read_csv(csvfile)
    df.loc[0, "birth_year"] = 666
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert "has differing birth_year field" in str(exc.value)


def test_csv_new_assignment(csvfile):
    # Delete all current officers and assignments
    Assignment.query.delete()
    Officer.query.delete()

    assert Officer.query.count() == 0

    df = pd.read_csv(csvfile)
    df.loc[0, "job_title"] = "Commander"
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created > 0
    assert n_updated == 0
    assert Officer.query.count() == n_created

    officer = get_officer(
        1, df.loc[0, "star_no"], df.loc[0, "first_name"], df.loc[0, "last_name"]
    )
    assert officer
    officer_id = officer.id
    assert len(list(officer.assignments)) == 1

    # Update job_title
    df.loc[0, "job_title"] = "CAPTAIN"
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated == 1

    officer = Officer.query.filter_by(id=officer_id).one()
    assert len(list(officer.assignments)) == 2
    for assignment in officer.assignments:
        assert (
            assignment.job.job_title == "Commander"
            or assignment.job.job_title == "CAPTAIN"
        )


def test_csv_new_name(csvfile):
    df = pd.read_csv(csvfile)
    officer_uid = df.loc[0, "unique_internal_identifier"]
    assert officer_uid

    df.loc[0, "first_name"] = "FOO"
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated == 1

    officer = Officer.query.filter_by(unique_internal_identifier=officer_uid).one()

    assert officer.first_name == "FOO"


def test_csv_new_officer(csvfile):
    df = pd.read_csv(csvfile)

    n_rows = len(df.index)
    assert n_rows > 0

    n_officers = Officer.query.count()
    assert n_officers > 0

    new_uid = str(uuid.uuid4())
    new_officer = {  # Must match fields in csvfile
        "department_id": 1,
        "unique_internal_identifier": new_uid,
        "first_name": "FOO",
        "last_name": "BAR",
        "middle_initial": None,
        "suffix": None,
        "gender": "F",
        "race": "BLACK",
        "employment_date": None,
        "birth_year": None,
        "star_no": 666,
        "job_title": "CAPTAIN",
        "unit": None,
        "star_date": None,
        "resign_date": None,
        "salary": 1.23,
        "salary_year": 2019,
        "salary_is_fiscal_year": True,
        "overtime_pay": 4.56,
    }
    df = df.append([new_officer])
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 1
    assert n_updated == 0

    officer = Officer.query.filter_by(unique_internal_identifier=new_uid).one()

    assert officer.first_name == "FOO"
    assert Officer.query.count() == n_officers + 1


def test_csv_new_salary(csvfile):
    # Delete all current officers and salaries
    Salary.query.delete()
    Officer.query.delete()

    assert Officer.query.count() == 0

    df = pd.read_csv(csvfile)
    df.loc[0, "salary"] = "123456.78"
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created > 0
    assert n_updated == 0
    officer_count = Officer.query.count()
    assert officer_count == n_created

    officer = get_officer(
        1, df.loc[0, "star_no"], df.loc[0, "first_name"], df.loc[0, "last_name"]
    )
    assert officer
    officer_id = officer.id
    assert len(list(officer.salaries)) == 1

    # Update salary
    df.loc[0, "salary"] = "150000"
    df.to_csv(csvfile)

    assert Officer.query.count() > 0
    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated == 1
    assert Officer.query.count() == officer_count

    officer = Officer.query.filter_by(id=officer_id).one()
    assert len(list(officer.salaries)) == 2
    for salary in officer.salaries:
        assert float(salary.salary) == 123456.78 or float(salary.salary) == 150000.00


def test_bulk_add_officers__success(session, department_with_ranks, csv_path):
    # generate two officers with different names
    first_officer = generate_officer()
    first_officer.department = department_with_ranks
    print(Job.query.all())
    print(Job.query.filter_by(department=department_with_ranks).all())
    job = (
        Job.query.filter_by(department=department_with_ranks).filter_by(order=1)
    ).first()
    fo_fn = "Uniquefirst"
    first_officer.first_name = fo_fn
    fo_ln = first_officer.last_name
    session.add(first_officer)
    session.commit()
    assignment = Assignment(baseofficer=first_officer, job_id=job.id)
    session.add(assignment)
    session.commit()
    different_officer = generate_officer()
    different_officer.department = department_with_ranks
    different_officer.job = job
    do_fn = different_officer.first_name
    do_ln = different_officer.last_name
    session.add(different_officer)
    assignment = Assignment(baseofficer=different_officer, job=job)
    session.add(assignment)
    session.commit()

    department_id = department_with_ranks.id

    # generate csv to update one existing officer and add one new

    new_officer_first_name = "Newofficer"
    new_officer_last_name = "Name"

    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "job_title",
    ]
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department_id,
                "first_name": first_officer.first_name,
                "last_name": first_officer.last_name,
                "job_title": RANK_CHOICES_1[2],
            }
        )

        csv_writer.writerow(
            {
                "department_id": department_id,
                "first_name": new_officer_first_name,
                "last_name": new_officer_last_name,
                "job_title": RANK_CHOICES_1[1],
            }
        )

    # run command with generated csv
    result = run_command_print_output(bulk_add_officers, [csv_path, "--update-by-name"])

    # command had no errors & exceptions
    assert result.exit_code == 0
    assert result.exception is None

    # make sure that exactly three officers are assigned to the department now
    # and the first officer has two assignments stored (one original one
    # and one updated via csv)
    officer_query = Officer.query.filter_by(department_id=department_id)
    officers = officer_query.all()
    assert len(officers) == 3
    first_officer_db = officer_query.filter_by(first_name=fo_fn, last_name=fo_ln).one()
    assert {asmt.job.job_title for asmt in first_officer_db.assignments.all()} == {
        RANK_CHOICES_1[2],
        RANK_CHOICES_1[1],
    }
    different_officer_db = officer_query.filter_by(
        first_name=do_fn, last_name=do_ln
    ).one()
    assert [asmt.job.job_title for asmt in different_officer_db.assignments.all()] == [
        RANK_CHOICES_1[1]
    ]
    new_officer_db = officer_query.filter_by(
        first_name=new_officer_first_name, last_name=new_officer_last_name
    ).one()
    assert [asmt.job.job_title for asmt in new_officer_db.assignments.all()] == [
        RANK_CHOICES_1[1]
    ]


def test_bulk_add_officers__duplicate_name(session, department, csv_path):
    # two officers with the same name
    first_name = "James"
    last_name = "Smith"
    first_officer = generate_officer()
    first_officer.department = department
    first_officer.first_name = first_name
    first_officer.last_name = last_name
    session.add(first_officer)
    session.commit()

    different_officer = generate_officer()
    different_officer.department = department
    different_officer.first_name = first_name
    different_officer.last_name = last_name
    session.add(different_officer)
    session.commit()

    # a csv that refers to that name
    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "star_no",
    ]
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department.id,
                "first_name": "James",
                "last_name": "Smith",
                "star_no": 1234,
            }
        )

    # run command with generated csv and --update-by-name flag set
    result = run_command_print_output(bulk_add_officers, [csv_path, "--update-by-name"])

    # command does not execute successfully since the name is not unique
    assert result.exit_code != 0
    # command throws MultipleResultsFound error
    assert isinstance(result.exception, MultipleResultsFound)


def test_bulk_add_officers__write_static_null_field(session, department, csv_path):
    # start with an officer whose birth_year is missing
    officer = generate_officer()
    officer.birth_year = None
    officer.department = department
    session.add(officer)
    session.commit()
    fo_uuid = officer.unique_internal_identifier

    birth_year = 1983
    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "unique_internal_identifier",
        "birth_year",
    ]
    # generate csv that provides birth_year for that officer
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department.id,
                "first_name": officer.first_name,
                "last_name": officer.last_name,
                "unique_internal_identifier": fo_uuid,
                "birth_year": birth_year,
            }
        )

    # run command no flags set
    result = run_command_print_output(bulk_add_officers, [csv_path])

    # command successful
    assert result.exit_code == 0
    assert result.exception is None

    # officer information is updated in the database
    officer = Officer.query.filter_by(unique_internal_identifier=fo_uuid).one()
    assert officer.birth_year == birth_year


def test_bulk_add_officers__write_static_field_no_flag(session, department, csv_path):
    # officer with birth year set
    officer = generate_officer()
    old_birth_year = 1979
    officer.birth_year = old_birth_year
    officer.department = department
    session.add(officer)
    session.commit()
    fo_uuid = officer.unique_internal_identifier

    new_birth_year = 1983

    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "unique_internal_identifier",
        "birth_year",
    ]
    # generate csv that assigns different birth year to that officer
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department.id,
                "first_name": officer.first_name,
                "last_name": officer.last_name,
                "unique_internal_identifier": fo_uuid,
                "birth_year": new_birth_year,
            }
        )

    # run command, no flag
    result = run_command_print_output(bulk_add_officers, [csv_path])

    # command fails because birth year is a static field and cannot be changed
    # without --update-static-fields set
    assert result.exit_code != 0
    assert result.exception is not None

    # officer still has original birth year
    officer = Officer.query.filter_by(unique_internal_identifier=fo_uuid).one()
    assert officer.birth_year == old_birth_year


def test_bulk_add_officers__write_static_field__flag_set(session, department, csv_path):
    # officer with birth year set
    officer = generate_officer()
    officer.birth_year = 1979
    officer.department = department
    session.add(officer)
    session.commit()
    officer_uuid = officer.unique_internal_identifier

    new_birth_year = 1983

    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "unique_internal_identifier",
        "birth_year",
    ]
    # generate csv assigning different birth year to that officer
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department.id,
                "first_name": officer.first_name,
                "last_name": officer.last_name,
                "unique_internal_identifier": officer_uuid,
                "birth_year": new_birth_year,
            }
        )

    # run command with --update-static-fields set to allow
    # overwriting of birth year even if already present
    result = run_command_print_output(
        bulk_add_officers, [csv_path, "--update-static-fields"]
    )

    assert result.exit_code == 0
    assert result.exception is None

    # confirm that officer's birth year was updated in database
    officer = Officer.query.filter_by(unique_internal_identifier=officer_uuid).one()
    assert officer.birth_year == new_birth_year


def test_bulk_add_officers__no_create_flag(session, department, csv_path):
    # department with one officer
    department_id = department.id
    officer = generate_officer()
    officer.gender = "Not Sure"
    officer.department = department
    session.add(officer)
    session.commit()
    officer_uuid = officer.unique_internal_identifier
    officer_gender_updated = "M"

    fieldnames = [
        "department_id",
        "first_name",
        "last_name",
        "unique_internal_identifier",
        "gender",
    ]
    # generate csv that updates gender of officer already in database
    # and provides data for another (new) officer
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
        csv_writer.writeheader()

        csv_writer.writerow(
            {
                "department_id": department_id,
                "first_name": officer.first_name,
                "last_name": officer.last_name,
                "unique_internal_identifier": officer_uuid,
                "gender": officer_gender_updated,
            }
        )
        csv_writer.writerow(
            {
                "department_id": department_id,
                "first_name": "NewOfficer",
                "last_name": "NotInDatabase",
                "unique_internal_identifier": uuid.uuid4(),
                "gender": "M",
            }
        )

    # run bulk_add_officers command with --no-create flag set
    # so no new officers are created. Those that do not exist are
    # simply ignored
    result = run_command_print_output(bulk_add_officers, [csv_path, "--no-create"])

    assert result.exit_code == 0
    assert result.exception is None

    # confirm that only one officer is in database and information was updated
    officer = Officer.query.filter_by(department_id=department_id).one()
    assert officer.unique_internal_identifier == officer_uuid
    assert officer.gender == officer_gender_updated
