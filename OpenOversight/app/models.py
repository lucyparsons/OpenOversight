from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Officer(db.Model):
    __tablename__ = 'officers'

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(120), index=True, unique=False)
    first_name = db.Column(db.String(120), index=True, unique=False)
    middle_initial = db.Column(db.String(120), unique=False, nullable=True)
    race = db.Column(db.String(120), index=True, unique=False)
    gender = db.Column(db.String(120), index=True, unique=False)
    employment_date = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    birth_year = db.Column(db.Integer, index=True, unique=False, nullable=True)
    pd_id = db.Column(db.Integer, index=True, unique=False)
    assignments = db.relationship('Assignment', backref='officer', lazy='dynamic')
    face = db.relationship('Face', backref='officer', lazy='dynamic')
    def __repr__(self):
        return '<Officer ID {}: {} {} {}>'.format(self.id,
                                                  self.first_name,
                                                  self.middle_initial,
                                                  self.last_name)


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    star_no = db.Column(db.Integer, index=True, unique=False)
    rank = db.Column(db.String(120), index=True, unique=False)
    unit = db.Column(db.Integer, db.ForeignKey('unit_types.id'), nullable=True)
    star_date = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    resign_date = db.Column(db.DateTime, index=True, unique=False, nullable=True)

    def __repr__(self):
        return '<Assignment: ID {} : {}>'.format(self.officer_id,
                                                 self.star_no)


class Unit(db.Model):
    __tablename__ = 'unit_types'

    id = db.Column(db.Integer, primary_key=True)
    descrip = db.Column(db.String(120), index=True, unique=False)

    def __repr__(self):
        return '<Unit ID {}: {}>'.format(self.id, self.descrip)


class Face(db.Model):
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    img_id = db.Column(db.Integer, db.ForeignKey('raw_images.id'))
    face_position = db.Column(db.String(120), index=True, unique=False, nullable=True)  # No box dtype in SQLalchemy afaict
    image = db.relationship('Image', backref='face')
    user_tagging = db.relationship('User', backref='user_accounts')

    def __repr__(self):
        return '<Tag ID {}: {} - {}>'.format(self.id, self.officer_id, self.img_id)


class Image(db.Model):
    __tablename__ = 'raw_images'

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(120), unique=False)
    hash_img = db.Column(db.String(120), unique=False, nullable=True)

    # Track when the image was put into our database
    date_image_inserted = db.Column(db.DateTime, index=True, unique=False, nullable=True)

    # We might know when the image was taken e.g. through EXIF data
    date_image_taken = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    is_tagged = db.Column(db.Boolean, default=False, unique=False, nullable=True)

    def __repr__(self):
        return '<Image ID {}: {}>'.format(self.id, self.filepath)


class User(db.Model):
    __tablename__ = 'user_accounts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)
    registered_on = db.Column(db.DateTime)

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def __repr__(self):
        return '<User {}>'.format(self.username)