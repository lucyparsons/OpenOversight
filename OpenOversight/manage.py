from getpass import getpass
from sqlalchemy.orm.exc import NoResultFound

from flask_script import Manager, Server, Shell

from app import app
from app.models import db, User


manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=3000))


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


if __name__ == "__main__":
    manager.run()
