from pytest import raises
import time
from OpenOversight.app.models import (Officer, Assignment, Face, Image, Unit,
                                      User, db)

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
    user1 = User(password='bacon')
    user2 = User(password='bacon')
    assert user1.password_hash != user2.password_hash

def test_valid_confirmation_token(mockdata):
    user = User(password='bacon')
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token()
    assert user.confirm(token) is True

def test_invalid_confirmation_token(mockdata):
    user1 = User(password='bacon')
    user2 = User(password='bacon')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_confirmation_token()
    assert user2.confirm(token) is False

def test_expired_confirmation_token(mockdata):
    user = User(password='bacon')
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token(1)
    time.sleep(2)
    assert user.confirm(token) is False

def test_valid_reset_token(mockdata):
    user = User(password='bacon')
    db.session.add(user)
    db.session.commit()
    token = user.generate_reset_token()
    assert user.reset_password(token, 'vegan bacon') is True
    assert user.verify_password('vegan bacon') is True

def test_invalid_reset_token(mockdata):
    user1 = User(password='bacon')
    user2 = User(password='vegan bacon')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_reset_token()
    assert user2.reset_password(token, 'tempeh') is False
    assert user2.verify_password('vegan bacon') is True

def test_valid_email_change_token(mockdata):
    user = User(email='brian@example.com', password='bacon')
    db.session.add(user)
    db.session.commit()
    token = user.generate_email_change_token('lucy@example.org')
    assert user.change_email(token) is True
    assert user.email == 'lucy@example.org'

def test_invalid_email_change_token(mockdata):
    user1 = User(email='jen@example.com', password='cat')
    user2 = User(email='freddy@example.org', password='dog')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_email_change_token('mason@example.net')
    assert user2.change_email(token) is False
    assert user2.email == 'freddy@example.org'

def test_duplicate_email_change_token(mockdata):
    user1 = User(email='alice@example.com', password='cat')
    user2 = User(email='bob@example.org', password='dog')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user2.generate_email_change_token('alice@example.com')
    assert user2.change_email(token) is False
    assert user2.email == 'bob@example.org'
