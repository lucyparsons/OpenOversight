from __future__ import print_function
from builtins import input
from getpass import getpass
import sys
import csv

import click
from flask.cli import with_appcontext

from .models import db, Assignment, Department, Officer, User
from .utils import officer_exists


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
    with open(filename, 'r') as f:
        csvfile = csv.DictReader(f)
        departments = {}
        n_created = 0

        # Assert required fields are in CSV file
        required_fields = [
            'department_id',
            'first_name',
            'last_name',
        ]
        for field in required_fields:
            if field not in csvfile.fieldnames:
                raise Exception('Missing required field {}'.format(field))
        if 'badge' not in csvfile.fieldnames and 'unique_internal_identifier' not in csvfile.fieldnames:
            raise Exception('CSV file must include either badge numbers or unique identifiers for officers')

        for line in csvfile:
            department_id = line['department_id']
            department = departments.get(department_id)
            if line['department_id'] not in departments:
                department = Department.query.filter_by(id=department_id).one_or_none()
                if department:
                    departments[department_id] = department
                else:
                    raise Exception('Department ID {} not found'.format(department_id))

            # check for existing officer based on name
            if 'unique_internal_identifier' in csvfile.fieldnames and line['unique_internal_identifier']:
                if Officer.query.filter_by(
                    department_id=department_id,
                    unique_internal_identifier=line['unique_internal_identifier']
                ).one_or_none():
                    print('Skipping creation of existing officer with ID {} for department ID {}'.format(line['unique_internal_identifier'],
                                                                                                         department_id))
                    continue
            elif 'badge' in csvfile.fieldnames and line['badge']:
                if officer_exists(department_id, line['badge'], line['first_name'], line['last_name']):
                    print('Skipping creation of existing officer {} {} #{} for department ID {}'.format(line['first_name'],
                                                                                                        line['last_name'],
                                                                                                        line['badge'],
                                                                                                        department_id))
                    continue
            else:
                raise Exception('Officer {} {} missing badge number and unique identifier'.format(line['first_name'],
                                                                                                  line['last_name']))

            # create officer
            officer = Officer()
            officer.department_id = department_id
            officer.last_name = line['last_name']
            officer.first_name = line['first_name']
            if 'middle_initial' in csvfile.fieldnames:
                officer.middle_initial = line['middle_initial']
            if 'suffix' in csvfile.fieldnames:
                officer.suffix = line['suffix']
            if 'race' in csvfile.fieldnames:
                officer.race = line['race']
            if 'gender' in csvfile.fieldnames:
                officer.gender = line['gender']
            if 'employment_date' in csvfile.fieldnames:
                officer.employment_date = line['employment_date']
            if 'birth_year' in csvfile.fieldnames:
                officer.birth_year = line['birth_year']
            if 'unique_internal_identifier' in csvfile.fieldnames:
                officer.unique_internal_identifier = line['unique_internal_identifier']
            db.session.add(officer)
            db.session.commit()

            assignment = Assignment()
            assignment.officer_id = officer.id
            if 'badge' in csvfile.fieldnames:
                assignment.star_no = line['badge']
            if 'rank' in csvfile.fieldnames:
                assignment.rank = line['rank']
            if 'unit' in csvfile.fieldnames:
                assignment.unit = line['unit']
            if 'star_date' in csvfile.fieldnames:
                assignment.star_date = line['star_date']
            if 'resign_date' in csvfile.fieldnames:
                assignment.resign_date = line['resign_date']
            db.session.add(assignment)
            db.session.commit()

            n_created += 1
        print('Created {} officers'.format(n_created))
