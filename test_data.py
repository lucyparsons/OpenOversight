#!/usr/bin/python

import argparse
from datetime import datetime
import sys
import random

from OpenOversight.app import create_app, models
from OpenOversight.app.models import db

app = create_app('development')
db.app = app

NUM_OFFICERS = app.config['NUM_OFFICERS']
random.seed(app.config['SEED'])


OFFICERS = [('IVANA', '', 'TINKLE'),
            ('SEYMOUR', '', 'BUTZ'),
            ('HAYWOOD', 'U', 'CUDDLEME'),
            ('BEA', '', 'O\'PROBLEM'),
            ('URA', '', 'SNOTBALL'),
            ('HUGH', '', 'JASS'),
            ('OFFICER', '', 'BACON')]


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
    random_int = random.uniform(0, 1)
    if random_int >= 0.5:
        return models.Face(officer_id=officer.id,
                           img_id=random.choice(images).id)
    else:
        return False


def populate():
    """ Populate database with test data"""

    # Add images from Springfield Police Department
    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')
    image5 = models.Image(filepath='static/images/test_cop5.jpg')

    test_images = [image1, image2, image3, image4, image5]
    db.session.add_all(test_images)
    db.session.commit()

    officers = [generate_officer() for o in range(NUM_OFFICERS)]
    db.session.add_all(officers)
    db.session.commit()

    assignments = [build_assignment(officer) for officer in officers]
    db.session.add_all(assignments)
    db.session.commit()

    faces = [assign_faces(officer, test_images) for officer in officers]
    faces = [f for f in faces if f]

    db.session.add_all(faces)
    db.session.commit()

    test_user = models.User(email='test@example.org',
                            username='test_user',
                            password='testtest',
                            confirmed=True)
    db.session.add(test_user)
    db.session.commit()

    test_units = [models.Unit(descrip='District 13'),
                  models.Unit(descrip='Bureau of Organized Crime')]
    db.session.add_all(test_units)
    db.session.commit()


def cleanup():
    """ Cleanup database"""

    faces = models.Face.query.all()
    for face in faces:
        db.session.delete(face)

    officers = models.Officer.query.all()
    for po in officers:
        db.session.delete(po)

    assignments = models.Assignment.query.all()
    for assn in assignments:
        db.session.delete(assn)

    faces = models.Face.query.all()
    for face in faces:
        db.session.delete(face)

    users = models.User.query.all()
    for user in users:
        db.session.delete(user)

    units = models.Unit.query.all()
    for unit in units:
        db.session.delete(unit)
    # TODO: Reset primary keys on all these tables
    db.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--populate", action='store_true',
                        help="populate the database with test data")
    parser.add_argument("-c", "--cleanup", action='store_true',
                        help="delete all test data from the database")
    args = parser.parse_args()

    if args.populate:
        print("[*] Populating database with test data...")
        try:
            populate()
            print("[*] Completed successfully!")
        except Exception as e:
            print("[!] Encountered an unknown issue, exiting.")
            print(e)
            sys.exit(1)

    if args.cleanup:
        print("[*] Cleaning up database...")
        try:
            cleanup()
            print("[*] Completed successfully!")
        except:
            print("[!] Encountered an unknown issue, exiting.")
            sys.exit(1)
