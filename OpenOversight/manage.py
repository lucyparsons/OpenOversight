from getpass import getpass
import sys

from flask_script import Manager, Server, Shell
from flask_migrate import Migrate, MigrateCommand

from app import app
from app.models import db, User


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=3000))
manager.add_command("db", MigrateCommand)


def make_shell_context():
    return dict(app=app, db=db)


manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def make_admin_user():
    "Add confirmed administrator account"
    while True:
        username = raw_input("Username: ")
        user = User.query.filter_by(username=username).one_or_none()
        if user:
            print "Username is already in use"
        else:
            break

    while True:
        email = raw_input("Email: ")
        user = User.query.filter_by(email=email).one_or_none()
        if user:
            print "Email address already in use"
        else:
            break

    while True:
        password = getpass("Password: ")
        password_again = getpass("Type your password again: ")

        if password == password_again:
            break
        print "Passwords did not match"

    u = User(username=username, email=email, password=password,
             confirmed=True, is_administrator=True)
    db.session.add(u)
    db.session.commit()
    print "Administrator {} successfully added".format(username)
    app.logger.info('Administrator {} added with email {}'.format(username,
                                                                  email))


@manager.command
def link_images_to_department():
    """Link existing images to first department"""
    from app.models import Image, db
    images = Image.query.all()
    print "Linking images to first department:"
    for image in images:
        if not image.department_id:
            sys.stdout.write(".")
            image.department_id = 1
        else:
            print "Skipped! Department already assigned"
    db.session.commit()


@manager.command
def link_officers_to_department():
    """Links officers and units to first department"""
    from app.models import Officer, Unit, db

    officers = Officer.query.all()
    units = Unit.query.all()

    print "Linking officers and units to first department:"
    for item in officers + units:
        if not item.department_id:
            sys.stdout.write(".")
            item.department_id = 1
        else:
            print "Skipped! Object already assigned to department!"
    db.session.commit()


if __name__ == "__main__":
    manager.run()
