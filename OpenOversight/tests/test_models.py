from OpenOversight.app.models import Officer, Assignment, Face, Image, Unit

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

def test_unit(mockdata):
    unit = Unit.query.first()
    assert unit.__repr__() == '<Unit ID {}: {}>'.format(unit.id, unit.descrip)
