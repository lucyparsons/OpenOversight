from app.models import Officer, Assignment, Face, Image

def test_officer_repr(mockdata):
    officer = Officer.query.first()
    assert officer.__repr__() == '<Officer ID 1: IVANA None TINKLE>'

def test_assignment_repr(mockdata):
    assignment = Assignment.query.first()
    assert assignment.__repr__() == '<Assignment: ID 1 : 1234>'

def test_image_repr(mockdata):
    image = Image.query.first()
    assert image.__repr__() == '<Image ID {}: {}>'.format(image.id, image.filepath)

def test_face_repr(mockdata):
    face = Face.query.first()
    assert face.__repr__() == '<Tag ID {}: {} - {}>'.format(face.id, face.officer_id, face.img_id)
