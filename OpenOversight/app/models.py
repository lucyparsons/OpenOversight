from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin
from flask import current_app
from . import login_manager

db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True, nullable=False)
    short_name = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return '<Department ID {}: {}>'.format(self.id, self.name)


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
    department_id = db.Column(db.Integer)

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
    department_id = db.Column(db.Integer)

    def __repr__(self):
        return 'Unit: {}'.format(self.descrip)


class Face(db.Model):
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    img_id = db.Column(db.Integer, db.ForeignKey('raw_images.id'))
    face_position_x = db.Column(db.Integer, unique=False)
    face_position_y = db.Column(db.Integer, unique=False)
    face_width = db.Column(db.Integer, unique=False)
    face_height = db.Column(db.Integer, unique=False)
    image = db.relationship('Image', backref='faces')
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


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    is_administrator = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)

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
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
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
