from pytest import raises
from OpenOversight.app.models import (Officer, Assignment, Face, Image, Unit,
                                      User)

def test_officer_repr(mockdata):
    officer = Officer.query.first()
    assert officer.__repr__() == '<Officer ID {}: {} {} {}>'.format(officer.id, officer.first_name, officer.middle_initial, officer.last_name)

def test_assignment_repr(mockdata):
    assignment = Assignment.query.first()
    assert assignment.__repr__() == '<Assignment: ID {} : {}>'.format(assignment.id, assignment.star_no)

def test_image_repr(mockdata):
    image = Image.query.first()
    assert image.__repr__() == '<Image ID {}: {}>'.format(image.id, image.filepath)

def test_face_repr(mockdata):
    face = Face.query.first()
    assert face.__repr__() == '<Tag ID {}: {} - {}>'.format(face.id, face.officer_id, face.img_id)

def test_unit_repr(mockdata):
    unit = Unit.query.first()
    assert unit.__repr__() == '<Unit ID {}: {}>'.format(unit.id, unit.descrip)

def test_user_repr(mockdata):
    user = User(username='bacon')
    assert user.__repr__() == "<User '{}'>".format(user.username)

def test_password_not_printed(mockdata):
    user = User(password='bacon')
    with raises(AttributeError):
        user.password

def test_password_set_success(mockdata):
    user = User(password='bacon')
    assert user.password_hash is not None

def test_password_verification_success(mockdata):
    user = User(password='bacon')
    assert user.verify_password('bacon') is True

def test_password_verification_failure(mockdata):
    user = User(password='bacon')
    assert user.verify_password('vegan bacon') is False

def test_password_salting(mockdata):
    u1 = User(password='bacon')
    u2 = User(password='bacon')
    assert u1.password_hash != u2.password_hash
