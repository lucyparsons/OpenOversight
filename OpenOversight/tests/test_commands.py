import csv
import datetime
import operator
import os
import traceback
import uuid

import pandas as pd
import pytest
from click.testing import CliRunner
from sqlalchemy.orm.exc import MultipleResultsFound

from OpenOversight.app.commands import (
    add_department,
    add_job_title,
    advanced_csv_import,
    bulk_add_officers,
    create_officer_from_row,
)
from OpenOversight.app.models import (
    Assignment,
    Department,
    Incident,
    Job,
    Link,
    Officer,
    Salary,
    Unit,
)
from OpenOversight.app.utils.db import get_officer
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

    job_title = "New Rank"
    is_sworn = True
    order = 15

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

    # make sure Job is already included in db
    assert (
        Job.query.filter_by(
            job_title=job_title, is_sworn_officer=True, order=1, department=department
        ).first()
        is not None
    )

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
    # make sure Job is already included in db
    assert (
        Job.query.filter_by(
            job_title=job_title, is_sworn_officer=True, order=1, department=department
        ).first()
        is not None
    )

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


def test_csv_import_new(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
    # Delete all current officers
    Officer.query.delete()

    assert Officer.query.count() == 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created > 0
    assert Officer.query.count() == n_created
    assert n_updated == 0


def test_csv_import_update(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
    n_existing = Officer.query.count()

    assert n_existing > 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created == 0
    assert n_updated == 0
    assert Officer.query.count() == n_existing


def test_csv_import_idempotence(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
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


def test_csv_new_assignment(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
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


def test_csv_new_name(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
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


def test_csv_new_officer(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
    df = pd.read_csv(csvfile)

    n_rows = len(df.index)
    assert n_rows > 0

    n_officers = Officer.query.count()
    assert n_officers > 0

    new_uid = str(uuid.uuid4())
    new_officer = pd.DataFrame.from_dict(
        [
            {  # Must match fields in csvfile
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
        ]
    )
    df = pd.concat([df, new_officer])
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 1
    assert n_updated == 0

    officer = Officer.query.filter_by(unique_internal_identifier=new_uid).one()

    assert officer.first_name == "FOO"
    assert Officer.query.count() == n_officers + 1


def test_csv_new_salary(csvfile, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")
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


def test_bulk_add_officers__success(
    session, department_without_officers, csv_path, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda: "y")
    # generate two officers with different names
    first_officer = generate_officer(department_without_officers)
    print(Job.query.all())
    print(Job.query.filter_by(department=department_without_officers).all())
    job = (
        Job.query.filter_by(department=department_without_officers).filter_by(order=1)
    ).first()
    fo_fn = "Uniquefirst"
    first_officer.first_name = fo_fn
    fo_ln = first_officer.last_name
    session.add(first_officer)
    session.commit()
    assignment = Assignment(baseofficer=first_officer, job_id=job.id)
    session.add(assignment)
    session.commit()
    different_officer = generate_officer(department_without_officers)
    different_officer.job = job
    do_fn = different_officer.first_name
    do_ln = different_officer.last_name
    session.add(different_officer)
    assignment = Assignment(baseofficer=different_officer, job=job)
    session.add(assignment)
    session.commit()

    department_id = department_without_officers.id

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
    first_officer = generate_officer(department)
    first_officer.first_name = first_name
    first_officer.last_name = last_name
    session.add(first_officer)
    session.commit()

    different_officer = generate_officer(department)
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


def test_bulk_add_officers__write_static_null_field(
    session, department, csv_path, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda: "y")
    # start with an officer whose birth_year is missing
    officer = generate_officer(department)
    officer.birth_year = None
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
    officer = generate_officer(department)
    old_birth_year = 1979
    officer.birth_year = old_birth_year
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


def test_bulk_add_officers__write_static_field__flag_set(
    session, department, csv_path, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda: "y")
    # officer with birth year set
    officer = generate_officer(department)
    officer.birth_year = 1979
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


def test_bulk_add_officers__no_create_flag(
    session, department_without_officers, csv_path, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda: "y")
    # department with one officer
    department_id = department_without_officers.id
    officer = generate_officer(department_without_officers)
    officer.gender = None
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
    print(Officer.query.filter_by(department_id=department_id).all())
    officer = Officer.query.filter_by(department_id=department_id).one()
    assert officer.unique_internal_identifier == officer_uuid
    assert officer.gender == officer_gender_updated


def test_advanced_csv_import__success(session, department, test_csv_dir):
    # make sure department name aligns with the csv files
    assert department.name == "Springfield Police Department"

    # set up existing data
    officer = Officer(
        id=49483,
        department_id=1,
        first_name="Already",
        last_name="InDatabase",
        birth_year=1951,
    )
    session.add(officer)

    assignment = Assignment(
        id=77021,
        officer_id=officer.id,
        star_no="4567",
        star_date=datetime.date(2020, 1, 1),
        job_id=department.jobs[0].id,
    )
    session.add(assignment)

    salary = Salary(
        id=33001,
        salary=30000,
        officer_id=officer.id,
        year=2018,
        is_fiscal_year=False,
    )
    session.add(salary)

    incident = Incident(
        id=123456,
        report_number="Old_Report_Number",
        department_id=1,
        description="description",
        time=datetime.time(23, 45, 16),
    )
    incident.officers = [officer]
    session.add(incident)

    link = Link(id=55051, title="Existing Link", url="https://www.example.org")
    session.add(link)
    officer.links = [link]

    # run command with the csv files in the test_csvs folder
    result = run_command_print_output(
        advanced_csv_import,
        [
            str(department.name),
            "--officers-csv",
            os.path.join(test_csv_dir, "officers.csv"),
            "--assignments-csv",
            os.path.join(test_csv_dir, "assignments.csv"),
            "--salaries-csv",
            os.path.join(test_csv_dir, "salaries.csv"),
            "--links-csv",
            os.path.join(test_csv_dir, "links.csv"),
            "--incidents-csv",
            os.path.join(test_csv_dir, "incidents.csv"),
        ],
    )

    # command did not fail
    assert result.exception is None
    assert result.exit_code == 0

    print(list(Officer.query.all()))
    all_officers = {
        officer.unique_internal_identifier: officer
        for officer in Officer.query.filter_by(department_id=1).all()
    }
    # make sure all the data is imported as expected
    cop1 = all_officers["UID-1"]
    assert cop1.first_name == "Mark"
    assert cop1.last_name == "Smith"
    assert cop1.gender == "M"
    assert cop1.race == "WHITE"
    assert cop1.employment_date == datetime.date(2019, 7, 12)
    assert cop1.birth_year == 1984
    assert cop1.middle_initial == "O"
    assert cop1.suffix is None

    salary_2018, salary_2019 = sorted(cop1.salaries, key=operator.attrgetter("year"))
    assert salary_2018.year == 2018
    assert salary_2018.salary == 10000
    assert salary_2018.is_fiscal_year is True
    assert salary_2018.overtime_pay is None
    assert salary_2019.salary == 10001

    assignment_po, assignment_cap = sorted(
        cop1.assignments, key=operator.attrgetter("star_date")
    )
    assert assignment_po.star_no == "1234"
    assert assignment_po.star_date == datetime.date(2019, 7, 12)
    assert assignment_po.resign_date == datetime.date(2020, 1, 1)
    assert assignment_po.job.job_title == "Police Officer"
    assert assignment_po.unit_id is None

    assert assignment_cap.star_no == "2345"
    assert assignment_cap.job.job_title == "Captain"

    cop2 = all_officers["UID-2"]
    assert cop2.first_name == "Claire"
    assert cop2.last_name == "Fuller"
    assert cop2.suffix == "III"

    assert len(cop2.salaries) == 1
    assert cop2.salaries[0].salary == 20000

    assert len(cop2.assignments.all()) == 1
    assert cop2.assignments[0].job.job_title == "Commander"

    cop3 = all_officers["UID-3"]
    assert cop3.first_name == "Robert"
    assert cop3.last_name == "Brown"

    assert len(cop3.assignments.all()) == 0
    assert len(cop3.salaries) == 0

    cop4 = all_officers["UID-4"]
    assert cop4.id == 49483
    assert cop4.first_name == "Already"
    assert cop4.birth_year == 1952
    assert cop4.gender == "Other"
    assert cop4.salaries[0].salary == 50000

    assert len(cop4.assignments.all()) == 2
    updated_assignment, new_assignment = sorted(
        cop4.assignments, key=operator.attrgetter("star_date")
    )
    assert updated_assignment.job.job_title == "Police Officer"
    assert updated_assignment.resign_date == datetime.date(2020, 7, 10)
    assert updated_assignment.star_no == "4567"
    assert new_assignment.job.job_title == "Captain"
    assert new_assignment.star_date == datetime.date(2020, 7, 10)
    assert new_assignment.star_no == "54321"

    incident = cop4.incidents[0]
    assert incident.report_number == "CR-1234"
    license_plates = {plate.state: plate.number for plate in incident.license_plates}
    assert license_plates["NY"] == "ABC123"
    assert license_plates["IL"] == "98UMC"

    incident2 = Incident.query.filter_by(report_number="CR-9912").one()
    address = incident2.address
    assert address.street_name == "Fake Street"
    assert address.cross_street1 == "Main Street"
    assert address.cross_street2 is None
    assert address.city == "Chicago"
    assert address.state == "IL"
    assert address.zip_code == "60603"
    assert incident2.officers == [cop1]

    incident3 = Incident.query.get(123456)
    assert incident3.report_number == "CR-39283"
    assert incident3.description == "Don't know where it happened"
    assert incident3.officers == [cop1]
    assert incident3.date == datetime.date(2020, 7, 26)
    lp = incident3.license_plates[0]
    assert lp.number == "XYZ11"
    assert lp.state is None
    assert incident3.address is None
    assert incident3.time is None

    link_new = cop4.links[0]
    assert [link_new] == list(cop1.links)
    assert link_new.title == "A Link"
    assert link_new.url == "https://www.example.com"
    assert {officer.id for officer in link_new.officers} == {cop1.id, cop4.id}
    incident_link = incident2.links[0]
    assert incident_link.url == "https://www.example.com/incident"
    assert incident_link.title == "Another Link"
    assert incident_link.author == "Example Times"

    updated_link = Link.query.get(55051)
    assert updated_link.title == "Updated Link"
    assert updated_link.officers == []
    assert updated_link.incidents == [incident3]


def _create_csv(data, path, csv_file_name):
    csv_path = os.path.join(str(path), csv_file_name)
    field_names = set().union(*[set(row.keys()) for row in data])
    with open(csv_path, "w") as f:
        csv_writer = csv.DictWriter(f, field_names)
        csv_writer.writeheader()
        csv_writer.writerows(data)
    return csv_path


def test_advanced_csv_import__force_create(session, department, tmp_path):
    tmp_path = str(tmp_path)

    department_name = department.name

    other_department = Department(name="Other department", short_name="OPD")
    session.add(other_department)

    officer = Officer(
        id=99001,
        department_id=other_department.id,
        first_name="Already",
        last_name="InDatabase",
    )
    session.add(officer)
    session.flush()

    # create temporary csv files
    officers_data = [
        {
            "id": 99001,
            "department_name": department_name,
            "last_name": "Test",
            "first_name": "First",
        },
        {
            "id": 99002,
            "department_name": department_name,
            "last_name": "Test",
            "first_name": "Second",
        },
        {
            "id": 99003,
            "department_name": department_name,
            "last_name": "Test",
            "first_name": "Third",
        },
    ]

    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    assignments_data = [
        {
            "id": 98001,
            "officer_id": 99002,
            "job title": RANK_CHOICES_1[1],
            "badge number": "12345",
            "start date": "2020-07-24",
        }
    ]
    assignments_csv = _create_csv(assignments_data, tmp_path, "assignments.csv")

    salaries_data = [{"id": 77001, "officer_id": 99003, "year": 2019, "salary": 98765}]
    salaries_csv = _create_csv(salaries_data, tmp_path, "salaries.csv")

    incidents_data = [
        {
            "id": 66001,
            "officer_ids": "99002|99001",
            "department_name": department_name,
            "street_name": "Fake Street",
        }
    ]
    incidents_csv = _create_csv(incidents_data, tmp_path, "incidents.csv")

    links_data = [
        {
            "id": 55001,
            "officer_ids": "99001",
            "incident_ids": "",
            "url": "https://www.example.org/3629",
        }
    ]
    links_csv = _create_csv(links_data, tmp_path, "links.csv")

    # run command with --force-create
    result = run_command_print_output(
        advanced_csv_import,
        [
            str(department.name),
            "--officers-csv",
            officers_csv,
            "--assignments-csv",
            assignments_csv,
            "--salaries-csv",
            salaries_csv,
            "--incidents-csv",
            incidents_csv,
            "--links-csv",
            links_csv,
            "--force-create",
        ],
    )

    # make sure command did not fail
    assert result.exception is None
    assert result.exit_code == 0

    # make sure all the data is imported as expected
    cop1 = Officer.query.get(99001)
    assert cop1.first_name == "First"

    cop2 = Officer.query.get(99002)
    assert cop2.assignments[0].star_no == "12345"
    assert cop2.assignments[0] == Assignment.query.get(98001)

    cop3 = Officer.query.get(99003)
    assert cop3.salaries[0].salary == 98765
    assert cop3.salaries[0] == Salary.query.get(77001)

    incident = Incident.query.get(66001)
    assert incident.address.street_name == "Fake Street"
    assert cop1.incidents[0] == incident
    assert cop2.incidents[0] == incident

    link = Link.query.get(55001)
    assert link.url == "https://www.example.org/3629"
    assert cop1.links[0] == link


def test_advanced_csv_import__overwrite_assignments(session, department, tmp_path):
    tmp_path = str(tmp_path)

    department_name = department.name

    other_department = Department(name="Other department", short_name="OPD")
    session.add(other_department)

    cop1_id = 999001
    cop2_id = 999002
    officer = Officer(
        id=cop1_id,
        department_id=department.id,
        first_name="Already",
        last_name="InDatabase",
    )
    officer2 = Officer(
        id=cop2_id,
        department_id=department.id,
        first_name="Also",
        last_name="InDatabase",
    )
    a1_id = 999101
    a2_id = 999102
    assignment = Assignment(
        id=a1_id,
        officer_id=officer.id,
        job_id=Job.query.filter_by(job_title="Police Officer").first().id,
    )
    assignment2 = Assignment(
        id=a2_id,
        officer_id=officer2.id,
        job_id=Job.query.filter_by(job_title="Police Officer").first().id,
    )
    session.add(officer)
    session.add(assignment)
    session.add(officer2)
    session.add(assignment2)
    session.flush()

    # create temporary csv files
    officers_data = [
        {
            "id": "#1",
            "department_name": department_name,
            "last_name": "Test",
            "first_name": "Second",
        },
    ]

    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    b1 = "12345"
    b2 = "999"
    assignments_data = [
        {
            "officer_id": cop1_id,
            "job title": "Captain",
            "badge number": b1,
            "start date": "2020-07-24",
        },
        {
            "officer_id": "#1",
            "job title": "Police Officer",
            "badge number": b2,
            "start date": "2020-07-21",
        },
    ]
    assignments_csv = _create_csv(assignments_data, tmp_path, "assignments.csv")

    # run command with --overwrite-assignments
    result = run_command_print_output(
        advanced_csv_import,
        [
            str(department.name),
            "--officers-csv",
            officers_csv,
            "--assignments-csv",
            assignments_csv,
            "--overwrite-assignments",
        ],
    )

    # make sure command did not fail
    assert result.exception is None
    assert result.exit_code == 0

    # make sure all the data is imported as expected
    cop1 = Officer.query.get(cop1_id)
    assert len(cop1.assignments.all()) == 1
    assert cop1.assignments[0].star_no == b1

    cop2 = Officer.query.get(cop2_id)
    assert len(cop2.assignments.all()) == 1
    assert cop2.assignments[0] == Assignment.query.get(a2_id)

    cop3 = Officer.query.filter_by(first_name="Second", last_name="Test").first()
    assert len(cop3.assignments.all()) == 1
    assert cop3.assignments[0].star_no == b2
    assert cop3.assignments[0].job.job_title == "Police Officer"


def test_advanced_csv_import__extra_fields_officers(session, department, tmp_path):
    department_name = department.name
    # create csv with invalid field 'name'
    officers_data = [
        {"id": "", "department_name": department_name, "name": "John Smith"},
    ]
    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    # run command
    result = run_command_print_output(
        advanced_csv_import,
        [str(department.name), "--officers-csv", officers_csv],
    )

    # expect the command to fail because of unexpected field 'name'
    assert result.exception is not None
    assert "unexpected" in str(result.exception).lower()
    assert "name" in str(result.exception)


def test_advanced_csv_import__missing_required_field_officers(
    session, department, tmp_path
):
    department_name = department.name
    # create csv with missing field 'id'
    officers_data = [
        {
            "department_name": department_name,
            "first_name": "John",
            "last_name": "Smith",
        },
    ]
    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    # run command
    result = run_command_print_output(
        advanced_csv_import,
        [str(department.name), "--officers-csv", officers_csv],
    )

    # expect the command to fail because 'id' is missing
    assert result.exception is not None
    assert "missing" in str(result.exception).lower()
    assert "id" in str(result.exception)


def test_advanced_csv_import__wrong_department(session, department, tmp_path):
    department_name = department.name
    other_department = Department(name="Other department", short_name="OPD")
    session.add(other_department)

    # create csv
    officers_data = [
        {
            "id": "",
            "department_name": department_name,
            "first_name": "John",
            "last_name": "Smith",
        },
    ]
    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    # run command with wrong department name
    result = run_command_print_output(
        advanced_csv_import,
        [other_department.name, "--officers-csv", officers_csv],
    )

    # expect command to fail because the department name provided to the
    # command is different than the one in the csv
    assert result.exception is not None
    assert result.exit_code != 0


def test_advanced_csv_import__update_officer_different_department(
    session, department, tmp_path
):
    department_name = department.name

    # set up data
    other_department = Department(name="Other department", short_name="OPD")
    session.add(other_department)
    officer = Officer(
        id=99021, department_id=other_department.id, first_name="Chris", last_name="Doe"
    )
    session.add(officer)

    # create csv to update the officer
    officers_data = [
        {
            "id": 99021,
            "department_name": department_name,
            "first_name": "John",
            "last_name": "Smith",
        },
    ]
    officers_csv = _create_csv(officers_data, tmp_path, "officers.csv")

    # run command
    result = run_command_print_output(
        advanced_csv_import,
        [str(department.name), "--officers-csv", officers_csv],
    )

    # command fails because the officer is assigned to a different department
    # and cannot be updated
    assert result.exception is not None
    assert result.exit_code != 0


def test_advanced_csv_import__unit_other_department(
    session, department, department_without_officers, tmp_path
):
    # set up data
    officer = generate_officer(department)
    session.add(officer)
    session.flush()
    session.add(department_without_officers)
    session.flush()
    unit = Unit(department_id=department_without_officers.id)
    session.add(unit)
    session.flush()

    # csv with unit_id referring to a unit in a different department
    assignments_data = [
        {
            "id": "",
            "officer_id": officer.id,
            "job title": RANK_CHOICES_1[1],
            "unit_id": unit.id,
        }
    ]
    assignments_csv = _create_csv(assignments_data, tmp_path, "assignments.csv")
    result = run_command_print_output(
        advanced_csv_import,
        [department.name, "--assignments-csv", assignments_csv],
    )

    # command fails because the unit does not belong to the department
    assert result.exception is not None
    assert result.exit_code != 0


def test_create_officer_from_row_adds_new_officer_and_normalizes_gender(
    app, session, department_without_officers
):
    with app.app_context():
        lookup_officer = Officer.query.filter_by(
            first_name="NewOfficerFromRow"
        ).one_or_none()
        assert lookup_officer is None

        row = {
            "gender": "Female",
            "first_name": "NewOfficerFromRow",
            "last_name": "Jones",
            "employment_date": "1980-12-01",
            "unique_internal_identifier": "officer-jones-unique-id",
        }
        create_officer_from_row(row, department_without_officers.id)

        lookup_officer = Officer.query.filter_by(
            first_name="NewOfficerFromRow"
        ).one_or_none()

        # Was an officer created in the database?
        assert lookup_officer is not None
        # Was the gender properly normalized?
        assert lookup_officer.gender == "F"
