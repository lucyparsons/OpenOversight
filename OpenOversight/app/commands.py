from __future__ import print_function
from builtins import input
from getpass import getpass
import sys

import click
from flask.cli import with_appcontext
from flask import current_app

from .models import db, User


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
