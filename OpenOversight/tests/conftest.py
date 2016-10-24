import os
import pytest

from app import create_app
from app import db as _db
from app import models
from datetime import datetime

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
    po1 = models.Officer(last_name='TINKLE', first_name='IVANA', race='BLACK',
			 gender='F', employment_date=datetime(2000, 4, 4, 1, 1, 1),
			 birth_year=1970, pd_id=1)
    po2 = models.Officer(last_name='JASS', first_name='HUGH', race='WHITE',
			 gender='M', birth_year=1950, pd_id=1,
			 employment_date=datetime(1996, 4, 4, 1, 1, 1))
    po3 = models.Officer(last_name='Butz', first_name='Seymour', race='WHITE',
			 gender='F', birth_year=1950, pd_id=1,
			 employment_date=datetime(1983, 4, 4, 1, 1, 1))
    po4 = models.Officer(last_name='CUDDLEME', first_name='HAYWOOD', middle_initial='U',
			 race='HISPANIC', gender='F', birth_year=1950, pd_id=1,
			 employment_date=datetime(2014, 4, 4, 1, 1, 1))
    po5 = models.Officer(last_name='KLOZOFF', first_name='OLIVER', middle_initial='U',
			 race='WHITE', gender='M', birth_year=1950, pd_id=1,
			 employment_date=datetime(2004, 4, 4, 1, 1, 1))
    po6 = models.Officer(last_name='O\'PROBLEM', first_name='BEA', middle_initial='U',
			 race='HISPANIC', gender='F', birth_year=1978, pd_id=1,
			 employment_date=datetime(2014, 4, 4, 1, 1, 1))

    test_officers = [po1, po2, po3, po4, po5, po6]
    session.add_all(test_officers)

    star1 = models.Assignment(star_no=1234, rank='COMMANDER', officer=po1)
    star2 = models.Assignment(star_no=5678, rank='PO', officer=po2)
    star3 = models.Assignment(star_no=9012, rank='CHIEF', officer=po3)
    star4 = models.Assignment(star_no=3456, rank='LIEUTENANT', officer=po4)
    star5 = models.Assignment(star_no=5227, rank='PO', officer=po5)
    star6 = models.Assignment(star_no=9120, rank='DEPUTY CHIEF', officer=po6)
    test_assignments = [star1, star2, star3, star4, star5, star6]
    session.add_all(test_assignments)

    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')

    test_images = [image1, image2, image3, image4]
    session.add_all(test_images)

    face1 = models.Face(officer_id=po1.id, img_id=image1.id)
    face2 = models.Face(officer_id=po2.id, img_id=image2.id)
    face3 = models.Face(officer_id=po3.id, img_id=image3.id)
    face4 = models.Face(officer_id=po4.id, img_id=image4.id)
    face5 = models.Face(officer_id=po1.id, img_id=image3.id)

    test_faces = [face1, face2, face3, face4, face5]
    session.add_all(test_faces)

    session.commit()

@pytest.fixture
def client(app, request):
    client = app.test_client()
    def teardown():
	pass
    request.addfinalizer(teardown)
    return client