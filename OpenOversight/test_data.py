#!/usr/bin/python

import argparse
from datetime import datetime
import sys

from app import db, models


def populate():
    """ Populate database with test data"""
    po1 = models.Officer(last_name='Tinkle', first_name='Ivana', race='BLACK',
                         gender='F', employment_date=datetime(2000, 4, 4, 1, 1, 1),
                         birth_year=1970, pd_id=1)
    po2 = models.Officer(last_name='Jass', first_name='Hugh', race='WHITE',
                         gender='M', birth_year=1950, pd_id=1,
                         employment_date=datetime(1996, 4, 4, 1, 1, 1))
    po3 = models.Officer(last_name='Butz', first_name='Seymour', race='WHITE',
                         gender='F', birth_year=1950, pd_id=1,
                         employment_date=datetime(1983, 4, 4, 1, 1, 1))
    po4 = models.Officer(last_name='Cuddleme', first_name='Haywood', middle_initial='U',
                         race='HISPANIC', gender='F', birth_year=1950, pd_id=1,
                         employment_date=datetime(2014, 4, 4, 1, 1, 1))
    po5 = models.Officer(last_name='Klozoff', first_name='Oliver', middle_initial='U',
                         race='WHITE', gender='M', birth_year=1950, pd_id=1,
                         employment_date=datetime(2004, 4, 4, 1, 1, 1))
    po6 = models.Officer(last_name='O\'Problem', first_name='Bea', middle_initial='U',
                         race='HISPANIC', gender='F', birth_year=1978, pd_id=1,
                         employment_date=datetime(2014, 4, 4, 1, 1, 1))

    test_officers = [po1, po2, po3, po4, po5, po6]
    db.session.add_all(test_officers)
    db.session.commit()

    star1 = models.Assignment(star_no=1234, rank='COMMANDER', officer=po1)
    star2 = models.Assignment(star_no=5678, rank='PO', officer=po2)
    star3 = models.Assignment(star_no=9012, rank='CHIEF', officer=po3)
    star4 = models.Assignment(star_no=3456, rank='LIEUTENANT', officer=po4)
    star5 = models.Assignment(star_no=5227, rank='PO', officer=po5)
    star6 = models.Assignment(star_no=9120, rank='DEPUTY CHIEF', officer=po6)

    test_assignments = [star1, star2, star3, star4, star5, star6]
    db.session.add_all(test_assignments)
    db.session.commit()

    image1 = models.Image(filepath='static/images/test_cop1.png')
    image2 = models.Image(filepath='static/images/test_cop2.png')
    image3 = models.Image(filepath='static/images/test_cop3.png')
    image4 = models.Image(filepath='static/images/test_cop4.png')

    test_images = [image1, image2, image3, image4]
    db.session.add_all(test_images)
    db.session.commit()

    face1 = models.Face(officer_id=po1.id, img_id=image1.id)
    face2 = models.Face(officer_id=po2.id, img_id=image2.id)
    face3 = models.Face(officer_id=po3.id, img_id=image3.id)
    face4 = models.Face(officer_id=po4.id, img_id=image4.id)
    face5 = models.Face(officer_id=po1.id, img_id=image3.id)

    test_faces = [face1, face2, face3, face4, face5]
    db.session.add_all(test_faces)
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
