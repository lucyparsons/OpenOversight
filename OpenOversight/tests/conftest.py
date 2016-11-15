import os
import pytest
from flask import current_app
from app import create_app
from app import db as _db
from app import models
from datetime import datetime
import random

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

def build_assignment(officer):
    return models.Assignment(star_no=pick_star(),
                      rank=pick_rank(),
                      officer=officer)

def assign_faces(officer, images):
    if random.uniform(0, 1) >= 0.5:
        return models.Face(officer_id=officer.id, img_id=random.choice(images).id)
    else:
        return False

@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    app = create_app('testing')

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
    # if os.path.exists(TESTDB_PATH):
    #     os.unlink(TESTDB_PATH)

    def teardown():
        _db.drop_all()
        # os.unlink(TESTDB_PATH)

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
def mockdata(session, request):
    NUM_OFFICERS = current_app.config['NUM_OFFICERS']
    SEED = current_app.config['SEED']
    random.seed(SEED)

    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')

    test_images = [image1, image2, image3, image4]
    officers = [generate_officer() for o in range(NUM_OFFICERS)]
    assignments = [build_assignment(officer) for officer in officers]
    faces = [assign_faces(officer, test_images) for officer in officers]
    faces = [f for f in faces if f]
    session.add_all(test_images)
    session.add_all(officers)
    session.add_all(assignments)
    session.add_all(faces)
    session.commit()
    return assignments[0].star_no

@pytest.fixture
def client(app, request):
    client = app.test_client()
    def teardown():
        pass
    request.addfinalizer(teardown)
    return client