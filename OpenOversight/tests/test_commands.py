from click.testing import CliRunner
from OpenOversight.app.commands import add_department, add_job_title
from OpenOversight.app.models import Department, Job


def test_add_department__success(session):
    name = "Added Police Department"
    short_name = "APD"
    unique_internal_identifier = "30ad0au239eas939asdj"

    # add department via command line
    runner = CliRunner()
    result = runner.invoke(add_department,
                           [name, short_name, unique_internal_identifier])

    # command ran successful
    assert result.exit_code == 0
    # department was added to database
    departments = Department.query.filter_by(
        unique_internal_identifier_label=unique_internal_identifier).all()
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
    runner = CliRunner()
    result = runner.invoke(add_department, [name, short_name, "2320wea0s9d03eas"])

    # fails because Department with this name already exists
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_department__missing_argument(session):
    runner = CliRunner()
    # running add-department command missing one argument
    result = runner.invoke(add_department, ["Name of Department"])

    # fails because short name is required argument
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_job_title__success(session):
    department = Department(name="Another Police Department",
                            short_name="APD")
    session.add(department)
    session.commit()

    department_id = department.id

    job_title = "Police Officer"
    is_sworn = True
    order = 1

    runner = CliRunner()
    result = runner.invoke(add_job_title,
                           [str(department_id), job_title,
                            str(is_sworn), str(order)])

    assert result.exit_code == 0

    jobs = Job.query.filter_by(department_id=department_id,
                               job_title=job_title).all()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_title == job_title
    assert job.is_sworn_officer == is_sworn
    assert job.order == order


def test_add_job_title__duplicate(session):
    department = Department(name="Another Police Department",
                            short_name="APD")
    session.add(department)
    session.commit()
    job_title = "Police Officer"
    is_sworn = True
    order = 1
    job = Job(job_title=job_title, is_sworn_officer=is_sworn,
              order=order, department=department)
    session.add(job)
    session.commit()

    # adding exact same job again via command
    runner = CliRunner()
    result = runner.invoke(add_department,
                           [str(department.id), job_title,
                            str(is_sworn), str(order)
                            ])

    # fails because this job already exists
    assert result.exit_code != 0
    assert result.exception is not None


def test_add_job_title__different_departments(session):
    department = Department(name="Another Police Department",
                            short_name="APD")
    session.add(department)
    session.commit()

    other_department = Department(name="Other Police Department",
                            short_name="OPD")
    session.add(other_department)
    session.commit()
    other_department_id = other_department.id

    job_title = "Police Officer"
    is_sworn = True
    order = 1
    job = Job(job_title=job_title, is_sworn_officer=is_sworn,
              order=order, department=department)
    session.add(job)
    session.commit()

    # adding samme job but for different department
    runner = CliRunner()
    result = runner.invoke(add_job_title,
                           [str(other_department_id), job_title,
                            str(is_sworn), str(order)
                            ])

    # success because this department doesn't have that title yet
    assert result.exit_code == 0

    jobs = Job.query.filter_by(department_id=other_department_id,
                               job_title=job_title).all()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.job_title == job_title
    assert job.is_sworn_officer == is_sworn
    assert job.order == order
