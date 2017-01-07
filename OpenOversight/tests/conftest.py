from datetime import datetime
from flask import current_app
import pytest
import random
from selenium import webdriver
import time
import threading
from xvfbwrapper import Xvfb

from OpenOversight.app import create_app
from OpenOversight.app import models
from OpenOversight.app.models import db as _db


OFFICERS = [('IVANA', '', 'TINKLE'),
            ('SEYMOUR', '', 'BUTZ'),
            ('HAYWOOD', 'U', 'CUDDLEME'),
            ('BEA', '', 'O\'PROBLEM'),
            ('URA', '', 'SNOTBALL'),
            ('HUGH', '', 'JASS')]

def pick_birth_date():
    return random.randint(1950, 2000)

def pick_race():
    return random.choice(['WHITE', 'BLACK', 'HISPANIC', 'ASIAN',
                         'PACIFIC ISLANDER'])

def pick_gender():
    return random.choice(['M', 'F'])

def pick_first():
    return random.choice(OFFICERS)[0]

def pick_middle():
    return random.choice(OFFICERS)[1]

def pick_last():
    return random.choice(OFFICERS)[2]

def pick_name():
    return (pick_first(), pick_middle(), pick_last())

def pick_rank():
    return random.choice(['COMMANDER', 'CAPTAIN', 'PO'])

def pick_star():
    return random.randint(1, 9999)

def generate_officer():
    year_born = pick_birth_date()
    f_name, m_initial, l_name = pick_name()
    return models.Officer(
        last_name=l_name, first_name=f_name,
        middle_initial=m_initial,
        race=pick_race(), gender=pick_gender(),
        birth_year=year_born,
        employment_date=datetime(year_born + 20, 4, 4, 1, 1, 1),
        pd_id=1
    )

def build_assignment(officer, unit):
    return models.Assignment(star_no=pick_star(),
                      rank=pick_rank(),
                      officer=officer)

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

        # Cleanup users table
        models.User.query.delete()
        session.commit()

    request.addfinalizer(teardown)
    return session

@pytest.fixture
def mockdata(session, request):
    NUM_OFFICERS = current_app.config['NUM_OFFICERS']
    SEED = current_app.config['SEED']
    random.seed(SEED)

    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')

    unit1 = models.Unit(descrip="test")

    test_images = [image1, image2, image3, image4]
    officers = [generate_officer() for o in range(NUM_OFFICERS)]
    assignments = [build_assignment(officer, unit1) for officer in officers]
    faces = [assign_faces(officer, test_images) for officer in officers]
    faces = [f for f in faces if f]
    session.add_all(test_images)
    session.add(unit1)
    session.add_all(officers)
    session.add_all(assignments)
    session.add_all(faces)

    test_user = models.User(email='jen@example.org',
                            username='test_user',
                            password='dog')
    session.add(test_user)
    session.commit()
    return assignments[0].star_no

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
    driver = webdriver.Firefox()
    # wait for browser to start up
    time.sleep(3)
    yield driver

    # shutdown server
    driver.get("http://localhost:5000/shutdown")
    time.sleep(3)

    # shutdown headless webdriver
    driver.quit()
    vdisplay.stop()
