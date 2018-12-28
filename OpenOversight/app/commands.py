from __future__ import print_function
from builtins import input
from getpass import getpass
import sys
import csv

import click
from flask.cli import with_appcontext
from flask import current_app

from .models import db, Assignment, Department, Officer, User
from .utils import get_officer


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
    current_app.logger.info('Administrator {} added with email {}'.format(username,
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
@click.argument('filename')
@with_appcontext
def bulk_add_officers(filename):
    """Bulk adds officers."""
    with open(filename, 'r') as f:
        csvfile = csv.DictReader(f)
        departments = {}
        n_created = 0
        n_updated = 0

        required_fields = [
            'department_id',
            'first_name',
            'last_name',
        ]

        # Assert required fields are in CSV file
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

            # check for existing officer based on unique ID or name/badge
            if 'unique_internal_identifier' in csvfile.fieldnames and line['unique_internal_identifier']:
                officer = Officer.query.filter_by(
                    department_id=department_id,
                    unique_internal_identifier=line['unique_internal_identifier']
                ).one_or_none()
            elif 'badge' in csvfile.fieldnames and line['badge']:
                officer = get_officer(department_id, line['badge'],
                                      line['first_name'], line['last_name'])
            else:
                raise Exception('Officer {} {} missing badge number and unique identifier'.format(line['first_name'],
                                                                                                  line['last_name']))

            if officer:
                # Name and gender are the only potentially changeable fields, so update those
                officer.last_name = line['last_name']
                officer.first_name = line['first_name']
                if 'middle_initial' in csvfile.fieldnames:
                    officer.middle_initial = line['middle_initial']
                if 'suffix' in csvfile.fieldnames:
                    officer.suffix = line['suffix']
                if 'gender' in csvfile.fieldnames:
                    officer.gender = line['gender']

                # The rest should be static
                static_fields = [
                    'unique_internal_identifier',
                    'race',
                    'employment_date',
                    'birth_year'
                ]
                for fieldname in static_fields:
                    if fieldname in csvfile.fieldnames and getattr(officer, fieldname) != line[fieldname]:
                        raise Exception('Officer {} {} has differing {} field. Old: {}, new: {}'.format(
                            officer.first_name,
                            officer.last_name,
                            fieldname,
                            getattr(officer, fieldname),
                            line[fieldname]
                        ))
                # Don't need to add officer to db.session b/c object already in session

                assignment_fields = [
                    'badge',
                    'rank',
                    'unit',
                    'star_date',
                    'resign_date'
                ]
                assignment_fields = list(filter(lambda x: x in csvfile.fieldnames, assignment_fields))
                assignments = Assignment.query.filter_by(
                    officer_id=officer.id
                ).all()
                match_assignment = False
                for assignment in assignments:
                    i = 0
                    for fieldname in assignment_fields:
                        if getattr(assignment, fieldname) == line[fieldname]:
                            i += 1
                    if i == len(assignment_fields):
                        match_assignment = True
                if not match_assignment:
                    # create new assignment
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

                n_updated += 1
            else:
                # create new officer
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
                db.session.flush()

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

                print('Added new officer {} {}'.format(officer.first_name, officer.last_name))
                n_created += 1

        db.session.commit()
        print('Created {} officers'.format(n_created))
        print('Updated {} officers'.format(n_updated))
