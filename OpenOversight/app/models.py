import datetime
import re
import time
from datetime import date
from decimal import Decimal

from authlib.jose import JoseError, JsonWebToken
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func

# from flask_sqlalchemy.model import DefaultMeta
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from . import login_manager
from .utils.constants import ENCODING_UTF_8
from .validators import state_validator, url_validator


db = SQLAlchemy()
jwt = JsonWebToken("HS512")

BaseModel = (
    db.Model
)  # This was here before but it's fucking with my IDE's typing - type: DefaultMeta (MJSB 2021-09-08)

officer_links = db.Table(
    "officer_links",
    db.Column("officer_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True),
    db.Column("link_id", db.Integer, db.ForeignKey("links.id"), primary_key=True),
)

officer_incidents = db.Table(
    "officer_incidents",
    db.Column("officer_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True),
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
)


date_updated_cache = TTLCache(maxsize=1024, ttl=12 * 60 * 60)


def _date_updated_cache_key(update_type: str):
    """Return a key function to calculate the cache key for Department
    `latest_*_update` methods using the department id and a given update type.

    Department.id is used instead of a Department obj because the default Python
    __hash__ is unique per obj instance, meaning multiple instances of the same
    department will have different hashes.

    Update type is used in the hash to differentiate between the (currently) three
    update types we compute per department.
    """

    def _cache_key(dept: "Department"):
        return hashkey(dept.id, update_type)

    return _cache_key


class Department(BaseModel):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True, nullable=False)
    short_name = db.Column(db.String(100), unique=False, nullable=False)

    # See https://github.com/lucyparsons/OpenOversight/issues/462
    unique_internal_identifier_label = db.Column(
        db.String(100), unique=False, nullable=True
    )

    def __repr__(self):
        return "<Department ID {}: {}>".format(self.id, self.name)

    def toCustomDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "unique_internal_identifier_label": self.unique_internal_identifier_label,
        }

    @cached(cache=date_updated_cache, key=_date_updated_cache_key("incident"))
    def latest_incident_update(self) -> datetime.date:
        incident_updated = (
            db.session.query(func.max(Incident.date_updated))
            .filter(Incident.department_id == self.id)
            .scalar()
        )
        return incident_updated.date() if incident_updated else None

    @cached(cache=date_updated_cache, key=_date_updated_cache_key("officer"))
    def latest_officer_update(self) -> datetime.date:
        officer_updated = (
            db.session.query(func.max(Officer.date_updated))
            .filter(Officer.department_id == self.id)
            .scalar()
        )
        return officer_updated.date() if officer_updated else None

    @cached(cache=date_updated_cache, key=_date_updated_cache_key("assignment"))
    def latest_assignment_update(self) -> datetime.date:
        assignment_updated = (
            db.session.query(func.max(Assignment.date_updated))
            .join(Officer)
            .filter(Assignment.officer_id == Officer.id)
            .filter(Officer.department_id == self.id)
            .scalar()
        )
        return assignment_updated.date() if assignment_updated else None


class Job(BaseModel):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), index=True, unique=False, nullable=False)
    is_sworn_officer = db.Column(db.Boolean, index=True, default=True)
    order = db.Column(db.Integer, index=True, unique=False, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="jobs")

    __table_args__ = (
        UniqueConstraint(
            "job_title", "department_id", name="unique_department_job_titles"
        ),
    )

    def __repr__(self):
        return "<Job ID {}: {}>".format(self.id, self.job_title)

    def __str__(self):
        return self.job_title


class Note(BaseModel):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    creator = db.relationship("User", backref="notes")
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    officer = db.relationship("Officer", back_populates="notes")
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)


class Description(BaseModel):
    __tablename__ = "descriptions"

    creator = db.relationship("User", backref="descriptions")
    officer = db.relationship("Officer", back_populates="descriptions")
    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)


class Officer(BaseModel):
    __tablename__ = "officers"

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(120), index=True, unique=False)
    first_name = db.Column(db.String(120), index=True, unique=False)
    middle_initial = db.Column(db.String(120), unique=False, nullable=True)
    suffix = db.Column(db.String(120), index=True, unique=False)
    race = db.Column(db.String(120), index=True, unique=False)
    gender = db.Column(db.String(5), index=True, unique=False, nullable=True)
    employment_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    birth_year = db.Column(db.Integer, index=True, unique=False, nullable=True)
    assignments = db.relationship("Assignment", backref="officer", lazy="dynamic")
    assignments_lazy = db.relationship("Assignment")
    face = db.relationship("Face", backref="officer")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="officers")
    unique_internal_identifier = db.Column(
        db.String(50), index=True, unique=True, nullable=True
    )
    date_created = db.Column(db.DateTime, default=func.now())
    date_updated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now(), index=True
    )

    links = db.relationship(
        "Link", secondary=officer_links, backref=db.backref("officers", lazy=True)
    )
    notes = db.relationship(
        "Note", back_populates="officer", order_by="Note.date_created"
    )
    descriptions = db.relationship(
        "Description", back_populates="officer", order_by="Description.date_created"
    )
    salaries = db.relationship(
        "Salary", back_populates="officer", order_by="Salary.year.desc()"
    )

    __table_args__ = (
        CheckConstraint("gender in ('M', 'F', 'Other')", name="gender_options"),
    )

    def full_name(self):
        if self.middle_initial:
            middle_initial = (
                self.middle_initial + "."
                if len(self.middle_initial) == 1
                else self.middle_initial
            )
            if self.suffix:
                return "{} {} {} {}".format(
                    self.first_name, middle_initial, self.last_name, self.suffix
                )
            else:
                return "{} {} {}".format(
                    self.first_name, middle_initial, self.last_name
                )
        if self.suffix:
            return "{} {} {}".format(self.first_name, self.last_name, self.suffix)
        return "{} {}".format(self.first_name, self.last_name)

    def race_label(self):
        if self.race is None:
            return "Data Missing"
        from .main.choices import RACE_CHOICES

        for race, label in RACE_CHOICES:
            if self.race == race:
                return label

    def gender_label(self):
        if self.gender is None:
            return "Data Missing"
        from .main.choices import GENDER_CHOICES

        for gender, label in GENDER_CHOICES:
            if self.gender == gender:
                return label

    def job_title(self):
        if self.assignments_lazy:
            return max(
                self.assignments_lazy, key=lambda x: x.star_date or date.min
            ).job.job_title

    def unit_descrip(self):
        if self.assignments_lazy:
            unit = max(
                self.assignments_lazy, key=lambda x: x.star_date or date.min
            ).unit
            return unit.descrip if unit else None

    def badge_number(self):
        if self.assignments_lazy:
            return max(
                self.assignments_lazy, key=lambda x: x.star_date or date.min
            ).star_no

    def currently_on_force(self):
        if self.assignments_lazy:
            most_recent = max(
                self.assignments_lazy, key=lambda x: x.star_date or date.min
            )
            return "Yes" if most_recent.resign_date is None else "No"
        return "Uncertain"

    def __repr__(self):
        if self.unique_internal_identifier:
            return "<Officer ID {}: {} {} {} {} ({})>".format(
                self.id,
                self.first_name,
                self.middle_initial,
                self.last_name,
                self.suffix,
                self.unique_internal_identifier,
            )
        return "<Officer ID {}: {} {} {} {}>".format(
            self.id, self.first_name, self.middle_initial, self.last_name, self.suffix
        )


class Currency(db.TypeDecorator):
    """
    Store currency as an integer in sqlite to avoid float conversion
    https://stackoverflow.com/questions/10355767/
    """

    impl = db.Numeric
    cache_ok = True

    def load_dialect_impl(self, dialect):
        typ = db.Numeric()
        if dialect.name == "sqlite":
            typ = db.Integer()
        return dialect.type_descriptor(typ)

    def process_bind_param(self, value, dialect):
        if dialect.name == "sqlite" and value is not None:
            value = int(Decimal(value) * 100)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == "sqlite" and value is not None:
            value = Decimal(value) / 100
        return value


class Salary(BaseModel):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    officer = db.relationship("Officer", back_populates="salaries")
    salary = db.Column(Currency(), index=True, unique=False, nullable=False)
    overtime_pay = db.Column(Currency(), index=True, unique=False, nullable=True)
    year = db.Column(db.Integer, index=True, unique=False, nullable=False)
    is_fiscal_year = db.Column(db.Boolean, index=False, unique=False, nullable=False)

    def __repr__(self):
        return "<Salary: ID {} : {}".format(self.officer_id, self.salary)


class Assignment(BaseModel):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    baseofficer = db.relationship("Officer")
    star_no = db.Column(db.String(120), index=True, unique=False, nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    job = db.relationship("Job")
    unit_id = db.Column(db.Integer, db.ForeignKey("unit_types.id"), nullable=True)
    unit = db.relationship("Unit")
    star_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    resign_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    date_created = db.Column(db.DateTime, default=func.now())
    date_updated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now(), index=True
    )

    def __repr__(self):
        return "<Assignment: ID {} : {}>".format(self.officer_id, self.star_no)


class Unit(BaseModel):
    __tablename__ = "unit_types"

    id = db.Column(db.Integer, primary_key=True)
    descrip = db.Column(db.String(120), index=True, unique=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship(
        "Department", backref="unit_types", order_by="Unit.descrip.asc()"
    )

    def __repr__(self):
        return "Unit: {}".format(self.descrip)


class Face(BaseModel):
    __tablename__ = "faces"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id"))
    img_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "raw_images.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="fk_face_image_id",
            use_alter=True,
        ),
    )
    original_image_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "raw_images.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
            use_alter=True,
            name="fk_face_original_image_id",
        ),
    )
    face_position_x = db.Column(db.Integer, unique=False)
    face_position_y = db.Column(db.Integer, unique=False)
    face_width = db.Column(db.Integer, unique=False)
    face_height = db.Column(db.Integer, unique=False)
    image = db.relationship("Image", backref="faces", foreign_keys=[img_id])
    original_image = db.relationship(
        "Image", backref="tags", foreign_keys=[original_image_id], lazy=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref="faces")
    featured = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (UniqueConstraint("officer_id", "img_id", name="unique_faces"),)

    def __repr__(self):
        return "<Tag ID {}: {} - {}>".format(self.id, self.officer_id, self.img_id)


class Image(BaseModel):
    __tablename__ = "raw_images"

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(255), unique=False)
    hash_img = db.Column(db.String(120), unique=False, nullable=True)

    # Track when the image was put into our database
    date_image_inserted = db.Column(
        db.DateTime, index=True, unique=False, nullable=True
    )

    # We might know when the image was taken e.g. through EXIF data
    date_image_taken = db.Column(db.DateTime, index=True, unique=False, nullable=True)
    contains_cops = db.Column(db.Boolean, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", backref="raw_images")
    is_tagged = db.Column(db.Boolean, default=False, unique=False, nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="raw_images")

    def __repr__(self):
        return "<Image ID {}: {}>".format(self.id, self.filepath)


incident_links = db.Table(
    "incident_links",
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column("link_id", db.Integer, db.ForeignKey("links.id"), primary_key=True),
)

incident_license_plates = db.Table(
    "incident_license_plates",
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column(
        "license_plate_id",
        db.Integer,
        db.ForeignKey("license_plates.id"),
        primary_key=True,
    ),
)

incident_officers = db.Table(
    "incident_officers",
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column(
        "officers_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True
    ),
)


class Location(BaseModel):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(100), index=True)
    cross_street1 = db.Column(db.String(100), unique=False)
    cross_street2 = db.Column(db.String(100), unique=False)
    city = db.Column(db.String(100), unique=False, index=True)
    state = db.Column(db.String(2), unique=False, index=True)
    zip_code = db.Column(db.String(5), unique=False, index=True)

    @validates("zip_code")
    def validate_zip_code(self, key, zip_code):
        if zip_code:
            zip_re = r"^\d{5}$"
            if not re.match(zip_re, zip_code):
                raise ValueError("Not a valid zip code")
            return zip_code

    @validates("state")
    def validate_state(self, key, state):
        return state_validator(state)

    def __repr__(self):
        if self.street_name and self.cross_street2:
            return "Intersection of {} and {}, {} {}".format(
                self.street_name, self.cross_street2, self.city, self.state
            )
        elif self.street_name and self.cross_street1:
            return "Intersection of {} and {}, {} {}".format(
                self.street_name, self.cross_street1, self.city, self.state
            )
        elif self.street_name and self.cross_street1 and self.cross_street2:
            return "Intersection of {} between {} and {}, {} {}".format(
                self.street_name,
                self.cross_street1,
                self.cross_street2,
                self.city,
                self.state,
            )
        else:
            return "{} {}".format(self.city, self.state)


class LicensePlate(BaseModel):
    __tablename__ = "license_plates"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(8), nullable=False, index=True)
    state = db.Column(db.String(2), index=True)
    # for use if car is federal, diplomat, or other non-state
    # non_state_identifier = db.Column(db.String(20), index=True)

    @validates("state")
    def validate_state(self, key, state):
        return state_validator(state)


class Link(BaseModel):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    url = db.Column(db.Text(), nullable=False)
    link_type = db.Column(db.String(100), index=True)
    description = db.Column(db.Text(), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    creator = db.relationship("User", backref="links", lazy=True)

    @validates("url")
    def validate_url(self, key, url):
        return url_validator(url)


class Incident(BaseModel):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, index=True)
    time = db.Column(db.Time, unique=False, index=True)
    report_number = db.Column(db.String(50), index=True)
    description = db.Column(db.Text(), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey("locations.id"))
    address = db.relationship("Location", backref="incidents")
    license_plates = db.relationship(
        "LicensePlate",
        secondary=incident_license_plates,
        lazy="subquery",
        backref=db.backref("incidents", lazy=True),
    )
    links = db.relationship(
        "Link",
        secondary=incident_links,
        lazy="subquery",
        backref=db.backref("incidents", lazy=True),
    )
    officers = db.relationship(
        "Officer",
        secondary=officer_incidents,
        lazy="subquery",
        backref=db.backref("incidents"),
    )
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="incidents", lazy=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    creator = db.relationship(
        "User", backref="incidents_created", lazy=True, foreign_keys=[creator_id]
    )
    last_updated_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    last_updated_by = db.relationship(
        "User", backref="incidents_updated", lazy=True, foreign_keys=[last_updated_id]
    )
    date_created = db.Column(db.DateTime, default=func.now())
    date_updated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now(), index=True
    )


class User(UserMixin, BaseModel):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    is_area_coordinator = db.Column(db.Boolean, default=False)
    ac_department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    ac_department = db.relationship(
        "Department", backref="coordinators", foreign_keys=[ac_department_id]
    )
    is_administrator = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)
    dept_pref = db.Column(db.Integer, db.ForeignKey("departments.id"))
    dept_pref_rel = db.relationship("Department", foreign_keys=[dept_pref])
    classifications = db.relationship("Image", backref="users")
    tags = db.relationship("Face", backref="users")

    def _jwt_encode(self, payload, expiration):
        secret = current_app.config["SECRET_KEY"]
        header = {"alg": "HS512"}

        now = int(time.time())
        payload["iat"] = now
        payload["exp"] = now + expiration

        return jwt.encode(header, payload, secret)

    def _jwt_decode(self, token):
        secret = current_app.config["SECRET_KEY"]
        token = jwt.decode(token, secret)
        token.validate()
        return token

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    @staticmethod
    def _case_insensitive_equality(field, value):
        return User.query.filter(func.lower(field) == func.lower(value))

    @staticmethod
    def by_email(email):
        return User._case_insensitive_equality(User.email, email)

    @staticmethod
    def by_username(username):
        return User._case_insensitive_equality(User.username, username)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        payload = {"confirm": self.id}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def confirm(self, token):
        try:
            data = self._jwt_decode(token)
        except JoseError as e:
            current_app.logger.warning("failed to decrypt token: %s", e)
            return False
        if data.get("confirm") != self.id:
            current_app.logger.warning(
                "incorrect id here, expected %s, got %s", data.get("confirm"), self.id
            )
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_reset_token(self, expiration=3600):
        payload = {"reset": self.id}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def reset_password(self, token, new_password):
        try:
            data = self._jwt_decode(token)
        except JoseError:
            return False
        if data.get("reset") != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        payload = {"change_email": self.id, "new_email": new_email}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def change_email(self, token):
        try:
            data = self._jwt_decode(token)
        except JoseError:
            return False
        if data.get("change_email") != self.id:
            return False
        new_email = data.get("new_email")
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    @property
    def is_active(self):
        """Override UserMixin.is_active to prevent disabled users from logging in."""
        return not self.is_disabled

    def __repr__(self):
        return "<User %r>" % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
