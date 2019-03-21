import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, BadData
from flask_login import UserMixin
from flask import current_app
from .validators import state_validator
from . import login_manager

db = SQLAlchemy()


officer_links = db.Table('officer_links',
                         db.Column('officer_id', db.Integer, db.ForeignKey('officers.id'), primary_key=True),
                         db.Column('link_id', db.Integer, db.ForeignKey('links.id'), primary_key=True))

officer_incidents = db.Table('officer_incidents',
                             db.Column('officer_id', db.Integer, db.ForeignKey('officers.id'), primary_key=True),
                             db.Column('incident_id', db.Integer, db.ForeignKey('incidents.id'), primary_key=True))


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True, nullable=False)
    short_name = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return '<Department ID {}: {}>'.format(self.id, self.name)


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    creator = db.relationship('User', backref='notes')
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id', ondelete='CASCADE'))
    officer = db.relationship('Officer', back_populates='notes')
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)


class Description(db.Model):
    __tablename__ = 'descriptions'

    creator = db.relationship('User', backref='descriptions')
    officer = db.relationship('Officer', back_populates='descriptions')
    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id', ondelete='CASCADE'))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)


class Officer(db.Model):
    __tablename__ = 'officers'

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(120), index=True, unique=False)
    first_name = db.Column(db.String(120), index=True, unique=False)
    middle_initial = db.Column(db.String(120), unique=False, nullable=True)
    suffix = db.Column(db.String(120), index=True, unique=False)
    race = db.Column(db.String(120), index=True, unique=False)
    gender = db.Column(db.String(120), index=True, unique=False)
    employment_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    birth_year = db.Column(db.Integer, index=True, unique=False, nullable=True)
    assignments = db.relationship('Assignment', backref='officer', lazy='dynamic')
    face = db.relationship('Face', backref='officer', lazy='dynamic')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='officers')
    unique_internal_identifier = db.Column(db.String(50), index=True, unique=True, nullable=True)
    # we don't expect to pull up officers via link often so we make it lazy.
    links = db.relationship(
        'Link',
        secondary=officer_links,
        lazy='subquery',
        backref=db.backref('officers', lazy=True))
    notes = db.relationship('Note', back_populates='officer', order_by='Note.date_created')
    descriptions = db.relationship('Description', back_populates='officer', order_by='Description.date_created')

    def full_name(self):
        if self.middle_initial:
            if self.suffix:
                return '{} {}. {} {}'.format(self.first_name, self.middle_initial, self.last_name, self.suffix)
            else:
                return '{} {}. {}'.format(self.first_name, self.middle_initial, self.last_name)
        if self.suffix:
                return '{} {} {}'.format(self.first_name, self.last_name, self.suffix)
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return '<Officer ID {}: {} {} {} {}>'.format(self.id,
                                                     self.first_name,
                                                     self.middle_initial,
                                                     self.last_name,
                                                     self.suffix)


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id', ondelete='CASCADE'))
    baseofficer = db.relationship('Officer')
    star_no = db.Column(db.String(120), index=True, unique=False, nullable=True)
    rank = db.Column(db.String(120), index=True, unique=False)
    unit = db.Column(db.Integer, db.ForeignKey('unit_types.id'), nullable=True)
    star_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    resign_date = db.Column(db.Date, index=True, unique=False, nullable=True)

    def __repr__(self):
        return '<Assignment: ID {} : {}>'.format(self.officer_id,
                                                 self.star_no)


class Unit(db.Model):
    __tablename__ = 'unit_types'

    id = db.Column(db.Integer, primary_key=True)
    descrip = db.Column(db.String(120), index=True, unique=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='unit_types')

    def __repr__(self):
        return 'Unit: {}'.format(self.descrip)


class Face(db.Model):
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    img_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'raw_images.id',
            ondelete='CASCADE',
            onupdate='CASCADE',
            name='fk_face_image_id',
            use_alter=True),
    )
    original_image_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'raw_images.id',
            ondelete='SET NULL',
            onupdate='CASCADE',
            use_alter=True,
            name='fk_face_original_image_id')
    )
    face_position_x = db.Column(db.Integer, unique=False)
    face_position_y = db.Column(db.Integer, unique=False)
    face_width = db.Column(db.Integer, unique=False)
    face_height = db.Column(db.Integer, unique=False)
    image = db.relationship('Image', backref='faces', foreign_keys=[img_id])
    original_image = db.relationship('Image', backref='tags', foreign_keys=[original_image_id], lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='faces')

    __table_args__ = (UniqueConstraint('officer_id', 'img_id',
                      name='unique_faces'), )

    def __repr__(self):
        return '<Tag ID {}: {} - {}>'.format(self.id, self.officer_id, self.img_id)


class Image(db.Model):
    __tablename__ = 'raw_images'

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(255), unique=False)
    hash_img = db.Column(db.String(120), unique=False, nullable=True)

    # Track when the image was put into our database
    date_image_inserted = db.Column(db.DateTime, index=True, unique=False, nullable=True)

    # We might know when the image was taken e.g. through EXIF data
    date_image_taken = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    contains_cops = db.Column(db.Boolean, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', backref='raw_images')
    is_tagged = db.Column(db.Boolean, default=False, unique=False, nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='raw_images')

    def __repr__(self):
        return '<Image ID {}: {}>'.format(self.id, self.filepath)


incident_links = db.Table(
    'incident_links',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.id'), primary_key=True),
    db.Column('link_id', db.Integer, db.ForeignKey('links.id'), primary_key=True)
)

incident_license_plates = db.Table(
    'incident_license_plates',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.id'), primary_key=True),
    db.Column('license_plate_id', db.Integer, db.ForeignKey('license_plates.id'), primary_key=True)
)

incident_officers = db.Table(
    'incident_officers',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.id'), primary_key=True),
    db.Column('officers_id', db.Integer, db.ForeignKey('officers.id'), primary_key=True)
)


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(100), index=True)
    cross_street1 = db.Column(db.String(100), unique=False)
    cross_street2 = db.Column(db.String(100), unique=False)
    city = db.Column(db.String(100), unique=False, index=True)
    state = db.Column(db.String(2), unique=False, index=True)
    zip_code = db.Column(db.String(5), unique=False, index=True)

    @validates('zip_code')
    def validate_zip_code(self, key, zip_code):
        if zip_code:
            zip_re = r'^\d{5}$'
            if not re.match(zip_re, zip_code):
                raise ValueError('Not a valid zip code')
            return zip_code

    @validates('state')
    def validate_state(self, key, state):
        return state_validator(state)

    def __repr__(self):
        if self.street_name and self.cross_street2:
            return 'Intersection of {} and {}, {} {}'.format(
                self.street_name, self.cross_street2, self.city, self.state)
        elif self.street_name and self.cross_street1:
            return 'Intersection of {} and {}, {} {}'.format(
                self.street_name, self.cross_street1, self.city, self.state)
        elif self.street_name and self.cross_street1 and self.cross_street2:
            return 'Intersection of {} between {} and {}, {} {}'.format(
                self.street_name, self.cross_street1, self.cross_street2,
                self.city, self.state)
        else:
            return '{} {}'.format(self.city, self.state)


class LicensePlate(db.Model):
    __tablename__ = 'license_plates'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(8), nullable=False, index=True)
    state = db.Column(db.String(2), index=True)
    # for use if car is federal, diplomat, or other non-state
    # non_state_identifier = db.Column(db.String(20), index=True)

    @validates('state')
    def validate_state(self, key, state):
        return state_validator(state)


class Link(db.Model):
    __tablename__ = 'links'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    url = db.Column(db.String(255), nullable=False)
    link_type = db.Column(db.String(100), index=True)
    description = db.Column(db.Text(), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='links', lazy=True)

    @validates('url')
    def validate_url(self, key, url):
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise ValueError('Not a valid URL')

        return url


class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, unique=False, index=True)
    report_number = db.Column(db.String(50), index=True)
    description = db.Column(db.Text(), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    address = db.relationship('Location', backref='incidents')
    license_plates = db.relationship('LicensePlate', secondary=incident_license_plates, lazy='subquery', backref=db.backref('incidents', lazy=True))
    links = db.relationship('Link', secondary=incident_links, lazy='subquery', backref=db.backref('incidents', lazy=True))
    officers = db.relationship(
        'Officer',
        secondary=officer_incidents,
        lazy='subquery',
        backref=db.backref('incidents'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department', backref='incidents', lazy=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', backref='incidents_created', lazy=True, foreign_keys=[creator_id])
    last_updated_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_updated_by = db.relationship('User', backref='incidents_updated', lazy=True, foreign_keys=[last_updated_id])


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    is_area_coordinator = db.Column(db.Boolean, default=False)
    ac_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    ac_department = db.relationship('Department', backref='coordinators', foreign_keys=[ac_department_id])
    is_administrator = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)
    dept_pref = db.Column(db.Integer, db.ForeignKey('departments.id'))
    dept_pref_rel = db.relationship('Department', foreign_keys=[dept_pref])
    classifications = db.relationship('Image', backref='users')
    tags = db.relationship('Face', backref='users')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password,
                                                    method='pbkdf2:sha256')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, BadData):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, BadData):
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, BadData):
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
