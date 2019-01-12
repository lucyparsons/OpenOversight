from datetime import datetime
from flask import current_app
import pytest
import random
from selenium import webdriver
import time
import threading
from xvfbwrapper import Xvfb
from faker import Faker
import csv
import uuid
import sys

from OpenOversight.app import create_app, models
from OpenOversight.app.utils import merge_dicts
from OpenOversight.app.models import db as _db

factory = Faker()


OFFICERS = [('IVANA', '', 'TINKLE'),
            ('SEYMOUR', '', 'BUTZ'),
            ('HAYWOOD', 'U', 'CUDDLEME'),
            ('BEA', '', 'O\'PROBLEM'),
            ('URA', '', 'SNOTBALL'),
            ('HUGH', '', 'JASS')]

RANK_CHOICES = ['COMMANDER', 'CAPTAIN', 'PO', 'Not Sure']

AC_DEPT = 1


def pick_birth_date():
    return random.randint(1950, 2000)


def pick_race():
    return random.choice(['WHITE', 'BLACK', 'HISPANIC', 'ASIAN',
                          'PACIFIC ISLANDER', 'Not Sure'])


def pick_gender():
    return random.choice(['M', 'F', 'Not Sure'])


def pick_first():
    return random.choice(OFFICERS)[0]


def pick_middle():
    return random.choice(OFFICERS)[1]


def pick_last():
    return random.choice(OFFICERS)[2]


def pick_name():
    return (pick_first(), pick_middle(), pick_last())


def pick_rank():
    return random.choice(RANK_CHOICES)


def pick_star():
    return random.randint(1, 9999)


def pick_department():
    departments = models.Department.query.all()
    return random.choice(departments)


def pick_uid():
    return str(uuid.uuid4())


def pick_salary():
    return random.randint(100, 100000000) / 100


def generate_officer():
    year_born = pick_birth_date()
    f_name, m_initial, l_name = pick_name()
    return models.Officer(
        last_name=l_name, first_name=f_name,
        middle_initial=m_initial,
        race=pick_race(), gender=pick_gender(),
        birth_year=year_born,
        employment_date=datetime(year_born + 20, 4, 4, 1, 1, 1),
        department_id=pick_department().id,
        unique_internal_identifier=pick_uid()
    )


def build_assignment(officer, unit):
    return models.Assignment(star_no=pick_star(), rank=pick_rank(),
                             officer=officer)


def build_note(officer, user):
    date = factory.date_time_this_year()
    return models.Note(
        text_contents=factory.text(),
        officer_id=officer.id,
        creator_id=user.id,
        date_created=date,
        date_updated=date)


def build_description(officer, user):
    date = factory.date_time_this_year()
    return models.Description(
        text_contents=factory.text(),
        officer_id=officer.id,
        creator_id=user.id,
        date_created=date,
        date_updated=date)


def build_salary(officer):
    return models.Salary(
        officer_id=officer.id,
        salary=pick_salary(),
        overtime_pay=pick_salary(),
        year=random.randint(2000, 2019),
        is_fiscal_year=True if random.randint(0, 1) else False)


def assign_faces(officer, images):
    if random.uniform(0, 1) >= 0.5:
        return models.Face(officer_id=officer.id,
                           img_id=random.choice(images).id)
    else:
        return False


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database."""

    def teardown():
        _db.drop_all()

    _db.app = app
    _db.create_all()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='function')
def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def mockdata(session):
    NUM_OFFICERS = current_app.config['NUM_OFFICERS']
    department = models.Department(name='Springfield Police Department',
                                   short_name='SPD')
    session.add(department)
    department2 = models.Department(name='Chicago Police Department',
                                    short_name='CPD')
    session.add(department2)
    session.commit()

    i = 0
    rank_choices = [_ for _ in RANK_CHOICES]
    rank_choices.insert(0, 'Not Sure')
    for rank in rank_choices:
        for department_id in [1, 2]:
            session.add(models.Rank(
                rank=rank,
                order=i,
                department_id=department_id
            ))
        i += 1
    session.commit()

    # Ensure test data is deterministic
    SEED = current_app.config['SEED']
    random.seed(SEED)

    unit1 = models.Unit(descrip="test")

    test_images = [models.Image(filepath='/static/images/test_cop{}.png'.format(x + 1), department_id=1) for x in range(5)] + \
        [models.Image(filepath='/static/images/test_cop{}.png'.format(x + 1), department_id=2) for x in range(5)]

    officers = [generate_officer() for o in range(NUM_OFFICERS)]
    session.add_all(officers)
    session.add_all(test_images)

    session.commit()

    all_officers = models.Officer.query.all()
    officers_dept1 = models.Officer.query.filter_by(department_id=1).all()
    officers_dept2 = models.Officer.query.filter_by(department_id=2).all()

    # assures that there are some assigned and unassigned images in each department
    assigned_images_dept1 = models.Image.query.filter_by(department_id=1).limit(3).all()

    assigned_images_dept2 = models.Image.query.filter_by(department_id=2).limit(2).all()

    assignments = [build_assignment(officer, unit1) for officer in all_officers]
    salaries = [build_salary(officer) for officer in all_officers]
    faces_dept1 = [assign_faces(officer, assigned_images_dept1) for officer in officers_dept1]
    faces_dept2 = [assign_faces(officer, assigned_images_dept2) for officer in officers_dept2]
    faces1 = [f for f in faces_dept1 if f]
    faces2 = [f for f in faces_dept2 if f]
    session.add(unit1)
    session.commit()
    session.add_all(assignments)
    session.add_all(salaries)
    session.add_all(faces1)
    session.add_all(faces2)

    test_user = models.User(email='jen@example.org',
                            username='test_user',
                            password='dog',
                            confirmed=True)
    session.add(test_user)

    test_admin = models.User(email='test@example.org',
                             username='test_admin',
                             password='testtest',
                             confirmed=True,
                             is_administrator=True)
    session.add(test_admin)

    test_area_coordinator = models.User(email='raq929@example.org',
                                        username='test_ac',
                                        password='horse',
                                        confirmed=True,
                                        is_area_coordinator=True,
                                        ac_department_id=AC_DEPT)
    session.add(test_area_coordinator)

    test_unconfirmed_user = models.User(email='freddy@example.org',
                                        username='b_meson',
                                        password='dog', confirmed=False)
    session.add(test_unconfirmed_user)
    session.commit()

    test_units = [models.Unit(descrip='District 13', department_id=1),
                  models.Unit(descrip='Bureau of Organized Crime',
                              department_id=1)]
    session.add_all(test_units)
    session.commit()

    test_addresses = [
        models.Location(
            street_name='Test St',
            cross_street1='Cross St',
            cross_street2='2nd St',
            city='My City',
            state='AZ',
            zip_code='23456'),
        models.Location(
            street_name='Testing St',
            cross_street1='First St',
            cross_street2='Fourth St',
            city='Another City',
            state='ME',
            zip_code='23456')
    ]

    session.add_all(test_addresses)
    session.commit()

    test_license_plates = [
        models.LicensePlate(number='603EEE', state='MA'),
        models.LicensePlate(number='404301', state='WA')
    ]

    session.add_all(test_license_plates)
    session.commit()

    test_links = [
        models.Link(url='https://stackoverflow.com/', link_type='link'),
        models.Link(url='http://www.youtube.com/?v=help', link_type='video')
    ]

    session.add_all(test_links)
    session.commit()

    test_incidents = [
        models.Incident(
            date=datetime(2016, 3, 16),
            report_number='42',
            description='A thing happened',
            department_id=1,
            address=test_addresses[0],
            license_plates=test_license_plates,
            links=test_links,
            officers=[all_officers[o] for o in range(4)],
            creator_id=1,
            last_updated_id=1
        ),
        models.Incident(
            date=datetime(2017, 12, 11),
            report_number='38',
            description='A thing happened',
            department_id=2,
            address=test_addresses[1],
            license_plates=[test_license_plates[0]],
            links=test_links,
            officers=[all_officers[o] for o in range(3)],
            creator_id=2,
            last_updated_id=1
        ),
    ]
    session.add_all(test_incidents)
    session.commit()

    users_that_can_create_notes = [test_admin, test_area_coordinator]

    # for testing routes
    first_officer = models.Officer.query.get(1)
    note = build_note(first_officer, test_admin)
    session.add(note)
    for officer in models.Officer.query.limit(20):
        user = random.choice(users_that_can_create_notes)
        note = build_note(officer, user)
        session.add(note)

    session.commit()

    users_that_can_create_descriptions = [test_admin, test_area_coordinator]

    # for testing routes
    first_officer = models.Officer.query.get(1)
    description = build_description(first_officer, test_admin)
    session.add(description)
    for officer in models.Officer.query.limit(20):
        user = random.choice(users_that_can_create_descriptions)
        description = build_description(officer, user)
        session.add(description)

    session.commit()

    return assignments[0].star_no


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
        'department_id',
        'unique_internal_identifier',
        'first_name',
        'last_name',
        'middle_initial',
        'suffix',
        'gender',
        'race',
        'employment_date',
        'birth_year',
        'star_no',
        'rank',
        'unit',
        'star_date',
        'resign_date',
        'salary',
        'salary_year',
        'salary_is_fiscal_year',
        'overtime_pay'
    ]

    officers_dept1 = models.Officer.query.filter_by(department_id=1).all()

    if sys.version_info.major == 2:
        csvf = open(str(csv_path), 'w')
    else:
        csvf = open(str(csv_path), 'w', newline='')
    try:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for officer in officers_dept1:
            if not officer.unique_internal_identifier:
                officer.unique_internal_identifier = str(uuid.uuid4())
            towrite = merge_dicts(vars(officer), {'department_id': 1})
            if len(list(officer.assignments)) > 0:
                assignment = officer.assignments[0]
                towrite = merge_dicts(towrite, vars(assignment))
            if len(list(officer.salaries)) > 0:
                salary = officer.salaries[0]
                towrite = merge_dicts(towrite, {
                    'salary': salary.salary,
                    'salary_year': salary.year,
                    'salary_is_fiscal_year': salary.is_fiscal_year,
                    'overtime_pay': salary.overtime_pay
                })
            writer.writerow(towrite)
    except:  # noqa E722
        raise
    finally:
        csvf.close()

    request.addfinalizer(teardown)
    return str(csv_path)


@pytest.fixture
def client(app, request):
    client = app.test_client()

    def teardown():
        pass
    request.addfinalizer(teardown)
    return client


@pytest.fixture
def browser(app, request):
    # start server
    threading.Thread(target=app.run).start()
    # give the server a few seconds to ensure it is up
    time.sleep(10)

    # start headless webdriver
    vdisplay = Xvfb()
    vdisplay.start()
    driver = webdriver.Firefox(log_path='/tmp/geckodriver.log')
    # wait for browser to start up
    time.sleep(3)
    yield driver

    # shutdown server
    driver.get("http://localhost:5000/shutdown")
    time.sleep(3)

    # shutdown headless webdriver
    driver.quit()
    vdisplay.stop()
