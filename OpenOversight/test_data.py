#!/usr/bin/python

import argparse
from datetime import datetime
import sys
import random

from app import create_app, db, models
app = create_app('development')
db.app = app

NUM_OFFICERS = 120
random.seed(666)


def pick_birth_date():
    return random.randint(1950, 2000)


def pick_race():
    return random.choice(['WHITE', 'BLACK', 'HISPANIC', 'ASIAN',
                         'PACIFIC ISLANDER'])


def pick_gender():
    return random.choice(['M', 'F'])


def pick_name():
    troll_cops = [('IVANA', '', 'TINKLE'),
                  ('Seymour', '', 'Butz'),
                  ('HAYWOOD', 'U', 'CUDDLEME'),
                  ('BEA', '', 'O\'PROBLEM'),
                  ('URA', '', 'SNOTBALL')]
    return random.choice(troll_cops)


def pick_rank():
    return random.choice(['COMMANDER', 'CAPTAIN', 'PO'])


def pick_star():
    return random.randint(1, 9999)


def populate():
    """ Populate database with test data"""

    # Add images from Springfield Police Department
    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')

    test_images = [image1, image2, image3, image4]
    db.session.add_all(test_images)
    db.session.commit()

    # Generate officers for Springfield Police Department
    for officer_id in range(NUM_OFFICERS):
        year_born = pick_birth_date()
        name = pick_name()
        test_officer = models.Officer(
            last_name=name[2], first_name=name[0],
            middle_initial=name[1],
            race=pick_race(), gender=pick_gender(),
            birth_year=year_born,
            employment_date=datetime(year_born + 20, 4, 4, 1, 1, 1),
            pd_id=1
            )

        db.session.add(test_officer)
        db.session.commit()

        test_assignment = models.Assignment(star_no=pick_star(),
                                            rank=pick_rank(),
                                            officer=test_officer)

        db.session.add(test_assignment)
        db.session.commit()

        # Not all officers should have faces
        if random.uniform(0, 1) >= 0.5:
            test_face = models.Face(officer_id=test_officer.id,
                                img_id=random.choice(test_images).id)
            db.session.add(test_face)
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

    # TODO: Reset primary keys on all these tables
    db.session.commit()


if __name__=="__main__":
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
