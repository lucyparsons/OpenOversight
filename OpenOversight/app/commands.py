from __future__ import print_function
from builtins import input
from getpass import getpass
import sys
import csv

import click
from flask.cli import with_appcontext

from .models import db, Assignment, Department, Officer, User
from .utils import badge_exists


# @manager.command
@click.command()
@with_appcontext
def make_admin_user():
    "Add confirmed administrator account"
    while True:
        username = input("Username: ")
        user = User.query.filter_by(username=username).one_or_none()
        if user:
            print("Username is already in use")
        else:
            break

    while True:
        email = input("Email: ")
        user = User.query.filter_by(email=email).one_or_none()
        if user:
            print("Email address already in use")
        else:
            break

    while True:
        password = getpass("Password: ")
        password_again = getpass("Type your password again: ")

        if password == password_again:
            break
        print("Passwords did not match")

    u = User(username=username, email=email, password=password,
             confirmed=True, is_administrator=True)
    db.session.add(u)
    db.session.commit()
    print("Administrator {} successfully added".format(username))
    app.logger.info('Administrator {} added with email {}'.format(username,
                                                                  email))


# @manager.command
@click.command()
@with_appcontext
def link_images_to_department():
    """Link existing images to first department"""
    from app.models import Image, db
    images = Image.query.all()
    print("Linking images to first department:")
    for image in images:
        if not image.department_id:
            sys.stdout.write(".")
            image.department_id = 1
        else:
            print("Skipped! Department already assigned")
    db.session.commit()


# @manager.command
@click.command()
@with_appcontext
def link_officers_to_department():
    """Links officers and units to first department"""
    from app.models import Officer, Unit, db

    officers = Officer.query.all()
    units = Unit.query.all()

    print("Linking officers and units to first department:")
    for item in officers + units:
        if not item.department_id:
            sys.stdout.write(".")
            item.department_id = 1
        else:
            print("Skipped! Object already assigned to department!")
    db.session.commit()


# @manager.command
@click.command()
@with_appcontext
def bulk_add_officers(filename):
    """Bulk adds officers."""
    csvfile = csv.DictReader(open(filename))
    departments = {}
    n_created = 0
    for line in csvfile:
        department_id = line['department_id']
        department = departments.get(department_id)
        if line['department_id'] not in departments:
            department = Department.query.filter_by(id=department_id).one_or_none()
            if department:
                departments[department_id] = department
            else:
                raise Exception('Department ID {} not found'.format(department_id))

        # check for existing officer based on badge
        if badge_exists(line['badge'], department_id):
            print 'Skipping creation of existing badge id {} for department id {}'.format(line['badge'], department_id)
            continue

        # create officer
        officer = Officer()
        officer.department_id = department_id
        officer.last_name = line['last_name']
        officer.first_name = line['first_name']
        officer.middle_initial = line['middle_initial']
        officer.race = line['race']
        officer.gender = line['gender']
        officer.employment_date = line['employment_date']
        officer.birth_year = line['birth_year']
        db.session.add(officer)
        db.session.commit()

        assignment = Assignment()
        assignment.officer_id = officer.id
        assignment.star_no = line['badge']
        assignment.rank = line['rank']
        db.session.add(assignment)
        db.session.commit()
        n_created += 1
    print 'created {} officers'.format(n_created)
