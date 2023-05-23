import csv
import datetime
import math
import os
import random
import sys
import threading
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import pytest
from faker import Faker
from flask import current_app
from PIL import Image as Pimage
from selenium import webdriver
from sqlalchemy.orm import scoped_session, sessionmaker
from xvfbwrapper import Xvfb

from OpenOversight.app import create_app, models
from OpenOversight.app.models import Job, Officer, Unit
from OpenOversight.app.models import db as _db
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.app.utils.general import merge_dicts
from OpenOversight.tests.routes.route_helpers import ADMIN_EMAIL, ADMIN_PASSWORD


factory = Faker()


OFFICERS = [
    ("IVANA", "", "TINKLE"),
    ("SEYMOUR", "", "BUTZ"),
    ("HAYWOOD", "U", "CUDDLEME"),
    ("BEA", "", "O'PROBLEM"),
    ("URA", "", "SNOTBALL"),
    ("HUGH", "", "JASS"),
]

RANK_CHOICES_1 = ["Not Sure", "Police Officer", "Captain", "Commander"]
RANK_CHOICES_2 = [
    "Not Sure",
    "Police Officer",
    "Lieutenant",
    "Sergeant",
    "Commander",
    "Chief",
]

DEPARTMENT_NAME = "Springfield Police Department"
OTHER_DEPARTMENT_NAME = "Chicago Police Department"
DEPARTMENT_WITHOUT_OFFICERS_NAME = "Empty Police Department"


AC_DEPT = 1


def pick_birth_date():
    return random.randint(1950, 2000)


def pick_date(seed: bytes = None, start_year=2000, end_year=2020):
    # source: https://stackoverflow.com/questions/40351791/how-to-hash-strings-into-a-float-in-01
    # Wanted to deterministically create a date from a seed string (e.g. the hash or uuid on an officer object)
    from hashlib import sha256
    from struct import unpack

    def bytes_to_float(b):
        return float(unpack("L", sha256(b).digest()[:8])[0]) / 2**64

    if seed is None:
        seed = str(uuid.uuid4()).encode(ENCODING_UTF_8)

    return datetime.datetime(start_year, 1, 1, 00, 00, 00) + datetime.timedelta(
        days=365 * (end_year - start_year) * bytes_to_float(seed)
    )


def pick_race():
    return random.choice(
        ["WHITE", "BLACK", "HISPANIC", "ASIAN", "PACIFIC ISLANDER", "Not Sure"]
    )


def pick_gender():
    return random.choice(["M", "F", "Other", None])


def pick_first():
    return random.choice(OFFICERS)[0]


def pick_middle():
    return random.choice(OFFICERS)[1]


def pick_last():
    return random.choice(OFFICERS)[2]


def pick_name():
    return (pick_first(), pick_middle(), pick_last())


def pick_star():
    return random.randint(1, 9999)


def pick_department():
    departments = models.Department.query.all()
    return random.choice(departments)


def pick_uid():
    return str(uuid.uuid4())


def pick_salary():
    return random.randint(100, 100000000) / 100


def generate_officer(department):
    year_born = pick_birth_date()
    f_name, m_initial, l_name = pick_name()
    return models.Officer(
        last_name=l_name,
        first_name=f_name,
        middle_initial=m_initial,
        race=pick_race(),
        gender=pick_gender(),
        birth_year=year_born,
        employment_date=datetime.datetime(year_born + 20, 4, 4, 1, 1, 1),
        department_id=department.id,
        unique_internal_identifier=pick_uid(),
    )


def build_assignment(officer: Officer, units: List[Optional[Unit]], jobs: Job):
    unit = random.choice(units)
    unit_id = unit.id if unit else None
    return models.Assignment(
        star_no=pick_star(),
        job_id=random.choice(jobs).id,
        officer=officer,
        unit_id=unit_id,
        star_date=pick_date(officer.full_name().encode(ENCODING_UTF_8)),
        resign_date=pick_date(officer.full_name().encode(ENCODING_UTF_8)),
    )


def build_note(officer, user, content=None):
    date = factory.date_time_this_year()
    if content is None:
        content = factory.text()
    return models.Note(
        text_contents=content,
        officer_id=officer.id,
        creator_id=user.id,
        date_created=date,
        date_updated=date,
    )


def build_description(officer, user, content=None):
    date = factory.date_time_this_year()
    if content is None:
        content = factory.text()
    return models.Description(
        text_contents=content,
        officer_id=officer.id,
        creator_id=user.id,
        date_created=date,
        date_updated=date,
    )


def build_salary(officer):
    return models.Salary(
        officer_id=officer.id,
        salary=pick_salary(),
        overtime_pay=pick_salary(),
        year=random.randint(2000, 2019),
        is_fiscal_year=True if random.randint(0, 1) else False,
    )


def assign_faces(officer, images):
    if random.uniform(0, 1) >= 0.5:
        img_id = random.choice(images).id
        return models.Face(
            officer_id=officer.id,
            img_id=img_id,
            original_image_id=img_id,
            featured=False,
        )
    else:
        return False


@pytest.fixture(scope="session")
def app(request):
    """Session-wide test `Flask` application."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture(autouse=True)
def ctx(app):
    with app.app_context():
        yield


@pytest.fixture(scope="session")
def db(app):
    """Session-wide test database."""

    with app.app_context():
        _db.app = app
        _db.create_all()
        connection = _db.engine.connect()
        session = scoped_session(session_factory=sessionmaker(bind=connection))
        _db.session = session
        add_mockdata(session)
        session.commit()
        connection.close()
        session.remove()

        yield _db


@pytest.fixture(scope="function")
def session(db):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    session = scoped_session(session_factory=sessionmaker(bind=connection))
    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def test_png_BytesIO():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, "images/204Cat.png")
    img = Pimage.open(local_path)

    byte_io = BytesIO()
    img.save(byte_io, img.format)
    byte_io.seek(0)
    return byte_io


@pytest.fixture
def test_jpg_BytesIO():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, "images/200Cat.jpeg")
    img = Pimage.open(local_path)

    byte_io = BytesIO()
    img.save(byte_io, img.format)
    byte_io.seek(0)
    return byte_io


@pytest.fixture
def test_csv_dir():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(test_dir, "test_csvs")


def add_mockdata(session):
    NUM_OFFICERS = current_app.config["NUM_OFFICERS"]
    assert NUM_OFFICERS >= 5
    department = models.Department(
        name=DEPARTMENT_NAME,
        short_name="SPD",
        unique_internal_identifier_label="homer_number",
    )
    session.add(department)
    department2 = models.Department(name=OTHER_DEPARTMENT_NAME, short_name="CPD")
    session.add(department2)
    empty_department = models.Department(
        name=DEPARTMENT_WITHOUT_OFFICERS_NAME, short_name="EPD"
    )
    session.add(empty_department)
    session.commit()

    for i, rank in enumerate(RANK_CHOICES_1):
        session.add(
            models.Job(
                job_title=rank,
                order=i,
                is_sworn_officer=True,
                department_id=department.id,
            )
        )
        session.add(
            models.Job(
                job_title=rank,
                order=i,
                is_sworn_officer=True,
                department_id=empty_department.id,
            )
        )

    for i, rank in enumerate(RANK_CHOICES_2):
        session.add(
            models.Job(
                job_title=rank,
                order=i,
                is_sworn_officer=True,
                department_id=department2.id,
            )
        )
    session.commit()

    # Ensure test data is deterministic
    SEED = current_app.config["SEED"]
    random.seed(SEED)

    test_units = [
        models.Unit(descrip="test", department_id=1),
        models.Unit(descrip="District 13", department_id=1),
        models.Unit(descrip="Donut Devourers", department_id=1),
        models.Unit(descrip="Bureau of Organized Crime", department_id=2),
        models.Unit(descrip="Porky's BBQ: Rub Division", department_id=2),
    ]
    session.add_all(test_units)
    session.commit()
    test_units.append(None)

    test_images = [
        models.Image(
            filepath=f"/static/images/test_cop{x+1}.png",
            department_id=department.id,
        )
        for x in range(5)
    ] + [
        models.Image(
            filepath=f"/static/images/test_cop{x+1}.png",
            department_id=department2.id,
        )
        for x in range(5)
    ]
    session.add_all(test_images)

    test_officer_links = [
        models.Link(
            url="https://openoversight.com/",
            link_type="link",
            title="OpenOversight",
            description="A public, searchable database of law enforcement officers.",
        ),
        models.Link(
            url="http://www.youtube.com/?v=help",
            link_type="video",
            title="Youtube",
            author="the internet",
        ),
    ]

    officers = []
    for d in [department, department2]:
        officers += [generate_officer(d) for _ in range(NUM_OFFICERS)]
    officers[0].links = test_officer_links
    session.add_all(officers)

    session.commit()

    all_officers = models.Officer.query.all()
    officers_dept1 = models.Officer.query.filter_by(department_id=1).all()
    officers_dept2 = models.Officer.query.filter_by(department_id=2).all()

    # assures that there are some assigned and unassigned images in each department
    assigned_images_dept1 = models.Image.query.filter_by(department_id=1).limit(3).all()
    assigned_images_dept2 = models.Image.query.filter_by(department_id=2).limit(3).all()

    jobs_dept1 = models.Job.query.filter_by(department_id=1).all()
    jobs_dept2 = models.Job.query.filter_by(department_id=2).all()

    # which percentage of officers have an assignment
    assignment_ratio = 0.9  # 90%
    num_officers_with_assignments_1 = math.ceil(len(officers_dept1) * assignment_ratio)
    assignments_dept1 = [
        build_assignment(officer, test_units, jobs_dept1)
        for officer in officers_dept1[:num_officers_with_assignments_1]
    ]
    num_officers_with_assignments_2 = math.ceil(len(officers_dept2) * assignment_ratio)
    assignments_dept2 = [
        build_assignment(officer, test_units, jobs_dept2)
        for officer in officers_dept2[:num_officers_with_assignments_2]
    ]

    salaries = [build_salary(officer) for officer in all_officers]
    faces_dept1 = [
        assign_faces(officer, assigned_images_dept1) for officer in officers_dept1
    ]
    faces_dept2 = [
        assign_faces(officer, assigned_images_dept2) for officer in officers_dept2
    ]
    faces1 = [f for f in faces_dept1 if f]
    faces2 = [f for f in faces_dept2 if f]
    session.commit()
    session.add_all(assignments_dept1)
    session.add_all(assignments_dept2)
    session.add_all(salaries)
    session.add_all(faces1)
    session.add_all(faces2)

    test_user = models.User(
        email="jen@example.org", username="test_user", password="dog", confirmed=True
    )
    session.add(test_user)

    test_admin = models.User(
        email=ADMIN_EMAIL,
        username="test_admin",
        password=ADMIN_PASSWORD,
        confirmed=True,
        is_administrator=True,
    )
    session.add(test_admin)

    test_area_coordinator = models.User(
        email="raq929@example.org",
        username="test_ac",
        password="horse",
        confirmed=True,
        is_area_coordinator=True,
        ac_department_id=AC_DEPT,
    )
    session.add(test_area_coordinator)

    test_unconfirmed_user = models.User(
        email="freddy@example.org", username="b_meson", password="dog", confirmed=False
    )
    session.add(test_unconfirmed_user)
    session.commit()

    test_disabled_user = models.User(
        email="may@example.org",
        username="may",
        password="yam",
        confirmed=True,
        is_disabled=True,
    )
    session.add(test_disabled_user)
    session.commit()

    test_modified_disabled_user = models.User(
        email="sam@example.org",
        username="sam",
        password="the yam",
        confirmed=True,
        is_disabled=True,
    )
    session.add(test_modified_disabled_user)
    session.commit()

    test_addresses = [
        models.Location(
            street_name="Test St",
            cross_street1="Cross St",
            cross_street2="2nd St",
            city="My City",
            state="AZ",
            zip_code="23456",
        ),
        models.Location(
            street_name="Testing St",
            cross_street1="First St",
            cross_street2="Fourth St",
            city="Another City",
            state="ME",
            zip_code="23456",
        ),
    ]

    session.add_all(test_addresses)
    session.commit()

    test_license_plates = [
        models.LicensePlate(number="603EEE", state="MA"),
        models.LicensePlate(number="404301", state="WA"),
    ]

    session.add_all(test_license_plates)
    session.commit()

    test_incident_links = [
        models.Link(
            url="https://stackoverflow.com/",
            link_type="link",
            creator=test_admin,
            creator_id=test_admin.id,
        ),
        models.Link(
            url="http://www.youtube.com/?v=help",
            link_type="video",
            creator=test_admin,
            creator_id=test_admin.id,
        ),
    ]

    session.add_all(test_incident_links)
    session.commit()

    test_incidents = [
        models.Incident(
            date=datetime.date(2016, 3, 16),
            time=datetime.time(4, 20),
            report_number="42",
            description="### A thing happened\n **Markup** description",
            department_id=1,
            address=test_addresses[0],
            license_plates=test_license_plates,
            links=test_incident_links,
            officers=[all_officers[o] for o in range(4)],
            creator_id=1,
            last_updated_id=1,
        ),
        models.Incident(
            date=datetime.date(2017, 12, 11),
            time=datetime.time(2, 40),
            report_number="38",
            description="A thing happened",
            department_id=2,
            address=test_addresses[1],
            license_plates=[test_license_plates[0]],
            links=test_incident_links,
            officers=[all_officers[o] for o in range(3)],
            creator_id=2,
            last_updated_id=1,
        ),
        models.Incident(
            date=datetime.datetime(2019, 1, 15),
            report_number="39",
            description=(
                Path(__file__).parent / "description_overflow.txt"
            ).read_text(),
            department_id=2,
            address=test_addresses[1],
            license_plates=[test_license_plates[0]],
            links=test_incident_links,
            officers=[all_officers[o] for o in range(1)],
            creator_id=2,
            last_updated_id=1,
        ),
    ]
    session.add_all(test_incidents)
    session.commit()

    users_that_can_create_notes = [test_admin, test_area_coordinator]

    # for testing routes
    first_officer = models.Officer.query.get(1)
    note = build_note(
        first_officer, test_admin, "### A markdown note\nA **test** note!"
    )
    session.add(note)
    for officer in models.Officer.query.limit(20):
        user = random.choice(users_that_can_create_notes)
        note = build_note(officer, user)
        session.add(note)

    session.commit()

    users_that_can_create_descriptions = [test_admin, test_area_coordinator]

    # for testing routes
    first_officer = models.Officer.query.get(1)
    description = build_description(
        first_officer, test_admin, "### A markdown description\nA **test** description!"
    )
    session.add(description)
    for officer in models.Officer.query.limit(20):
        user = random.choice(users_that_can_create_descriptions)
        description = build_description(officer, user)
        session.add(description)

    session.commit()

    return assignments_dept1[0].star_no


@pytest.fixture
def mockdata(session):
    pass


@pytest.fixture
def department(session):
    return models.Department.query.filter_by(name=DEPARTMENT_NAME).one()


@pytest.fixture
def department_without_officers(session):
    return models.Department.query.filter_by(
        name=DEPARTMENT_WITHOUT_OFFICERS_NAME
    ).one()


@pytest.fixture
def officer_no_assignments(department):
    return (
        Officer.query.filter_by(department_id=department.id)
        .outerjoin(Officer.assignments)
        .filter(Officer.assignments == None)  # noqa: E711
        .first()
    )


@pytest.fixture
def csv_path(tmp_path):
    return os.path.join(str(tmp_path), "file.csv")


@pytest.fixture
def csvfile(mockdata, tmp_path, request):
    csv_path = tmp_path / "dept1.csv"

    def teardown():
        try:
            csv_path.unlink()
        except:  # noqa: E722
            pass
        try:
            tmp_path.rmdir()
        except:  # noqa: E722
            pass

    teardown()
    tmp_path.mkdir()

    fieldnames = [
        "department_id",
        "unique_internal_identifier",
        "first_name",
        "last_name",
        "middle_initial",
        "suffix",
        "gender",
        "race",
        "employment_date",
        "birth_year",
        "star_no",
        "job_title",
        "unit_id",
        "star_date",
        "resign_date",
        "salary",
        "salary_year",
        "salary_is_fiscal_year",
        "overtime_pay",
    ]

    officers_dept1 = models.Officer.query.filter_by(department_id=1).all()

    if sys.version_info.major == 2:
        csvf = open(str(csv_path), "w")
    else:
        csvf = open(str(csv_path), "w", newline="")
    try:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for officer in officers_dept1:
            if not officer.unique_internal_identifier:
                officer.unique_internal_identifier = str(uuid.uuid4())
            towrite = merge_dicts(vars(officer), {"department_id": 1})
            if len(list(officer.assignments)) > 0:
                assignment = officer.assignments[0]
                towrite = merge_dicts(
                    towrite,
                    {
                        "star_no": assignment.star_no,
                        "job_title": assignment.job.job_title
                        if assignment.job
                        else None,
                        "unit_id": assignment.unit_id,
                        "star_date": assignment.star_date,
                        "resign_date": assignment.resign_date,
                    },
                )
            if len(list(officer.salaries)) > 0:
                salary = officer.salaries[0]
                towrite = merge_dicts(
                    towrite,
                    {
                        "salary": salary.salary,
                        "salary_year": salary.year,
                        "salary_is_fiscal_year": salary.is_fiscal_year,
                        "overtime_pay": salary.overtime_pay,
                    },
                )
            writer.writerow(towrite)
    finally:
        csvf.close()

    request.addfinalizer(teardown)
    return str(csv_path)


@pytest.fixture
def client(app):
    with app.app_context():
        client = app.test_client()
        yield client


@pytest.fixture(scope="session")
def worker_number(worker_id):
    if len(worker_id) < 2 or worker_id[:2] != "gw":
        return 0
    return int(worker_id[2:])


@pytest.fixture(scope="session")
def server_port(worker_number):
    return 5000 + worker_number


@pytest.fixture(scope="session")
def browser(app, server_port):
    # start server
    port = server_port
    print("Starting server at port {port}")
    threading.Thread(
        target=app.run, daemon=True, kwargs={"debug": False, "port": port}
    ).start()
    # give the server a few seconds to ensure it is up
    time.sleep(10)

    # start headless webdriver
    vdisplay = Xvfb()
    vdisplay.start()
    driver = webdriver.Firefox(log_path="/tmp/geckodriver.log")
    # wait for browser to start up
    time.sleep(3)
    yield driver

    # shutdown headless webdriver
    driver.quit()
    vdisplay.stop()
