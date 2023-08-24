import re
import time
import uuid
from datetime import date
from typing import List

from authlib.jose import JoseError, JsonWebToken
from cachetools import cached
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeMeta, declarative_mixin, declared_attr, validates
from sqlalchemy.sql import func as sql_func
from werkzeug.security import check_password_hash, generate_password_hash

from OpenOversight.app.models.database_cache import (
    DB_CACHE,
    model_cache_key,
    remove_database_cache_entries,
)
from OpenOversight.app.utils.choices import GENDER_CHOICES, RACE_CHOICES
from OpenOversight.app.utils.constants import (
    ENCODING_UTF_8,
    KEY_DB_CREATOR,
    KEY_DEPT_TOTAL_ASSIGNMENTS,
    KEY_DEPT_TOTAL_INCIDENTS,
    KEY_DEPT_TOTAL_OFFICERS,
    SIGNATURE_ALGORITHM,
)
from OpenOversight.app.validators import state_validator, url_validator


db = SQLAlchemy()
jwt = JsonWebToken(SIGNATURE_ALGORITHM)
BaseModel: DeclarativeMeta = db.Model


officer_links = db.Table(
    "officer_links",
    db.Column(
        "officer_id",
        db.Integer,
        db.ForeignKey("officers.id", name="officer_links_officer_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "link_id",
        db.Integer,
        db.ForeignKey("links.id", name="officer_links_link_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)

officer_incidents = db.Table(
    "officer_incidents",
    db.Column(
        "officer_id",
        db.Integer,
        db.ForeignKey("officers.id", name="officer_incidents_officer_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "incident_id",
        db.Integer,
        db.ForeignKey("incidents.id", name="officer_incidents_incident_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)


@declarative_mixin
class TrackUpdates:
    """Add columns to track the date of and user who created and last modified
    the object.
    """

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )
    last_updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    @declared_attr
    def created_by(cls):
        return db.Column(
            db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), unique=False
        )

    @declared_attr
    def last_updated_by(cls):
        return db.Column(
            db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), unique=False
        )

    @declared_attr
    def creator(cls):
        return db.relationship("User", foreign_keys=[cls.created_by])


class Department(BaseModel, TrackUpdates):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=False, unique=False, nullable=False)
    short_name = db.Column(db.String(100), unique=False, nullable=False)
    state = db.Column(db.String(2), server_default="", nullable=False)

    # See https://github.com/lucyparsons/OpenOversight/issues/462
    unique_internal_identifier_label = db.Column(
        db.String(100), unique=False, nullable=True
    )

    __table_args__ = (UniqueConstraint("name", "state", name="departments_name_state"),)

    def __repr__(self):
        return f"<Department ID {self.id}: {self.name} {self.state}>"

    def to_custom_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "state": self.state,
            "unique_internal_identifier_label": self.unique_internal_identifier_label,
        }

    @property
    def display_name(self):
        return self.name if not self.state else f"[{self.state}] {self.name}"

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_ASSIGNMENTS))
    def total_documented_assignments(self):
        return (
            db.session.query(Assignment.id)
            .join(Officer, Assignment.officer_id == Officer.id)
            .filter(Officer.department_id == self.id)
            .count()
        )

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_INCIDENTS))
    def total_documented_incidents(self):
        return (
            db.session.query(Incident).filter(Incident.department_id == self.id).count()
        )

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_OFFICERS))
    def total_documented_officers(self):
        return (
            db.session.query(Officer).filter(Officer.department_id == self.id).count()
        )

    def remove_database_cache_entries(self, update_types: List[str]) -> None:
        """Remove the Department model key from the cache if it exists."""
        remove_database_cache_entries(self, update_types)


class Job(BaseModel, TrackUpdates):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), index=True, unique=False, nullable=False)
    is_sworn_officer = db.Column(db.Boolean, index=True, default=True)
    order = db.Column(db.Integer, index=True, unique=False, nullable=False)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", name="jobs_department_id_fkey")
    )
    department = db.relationship("Department", backref="jobs")

    __table_args__ = (
        UniqueConstraint(
            "job_title", "department_id", name="unique_department_job_titles"
        ),
    )

    def __repr__(self):
        return f"<Job ID {self.id}: {self.job_title}>"

    def __str__(self):
        return self.job_title


class Note(BaseModel, TrackUpdates):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    officer = db.relationship("Officer", back_populates="notes")


class Description(BaseModel, TrackUpdates):
    __tablename__ = "descriptions"

    officer = db.relationship("Officer", back_populates="descriptions")
    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))


class Officer(BaseModel, TrackUpdates):
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
    assignments = db.relationship("Assignment", back_populates="base_officer")
    face = db.relationship("Face", backref="officer")
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", name="officers_department_id_fkey")
    )
    department = db.relationship("Department", backref="officers")
    unique_internal_identifier = db.Column(
        db.String(50), index=True, unique=True, nullable=True
    )

    links = db.relationship(
        "Link", secondary=officer_links, backref=db.backref("officers", lazy=True)
    )
    notes = db.relationship(
        "Note", back_populates="officer", order_by="Note.created_at"
    )
    descriptions = db.relationship(
        "Description", back_populates="officer", order_by="Description.created_at"
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
                return (
                    f"{self.first_name} {middle_initial} {self.last_name} {self.suffix}"
                )
            else:
                return f"{self.first_name} {middle_initial} {self.last_name}"
        if self.suffix:
            return f"{self.first_name} {self.last_name} {self.suffix}"
        return f"{self.first_name} {self.last_name}"

    def race_label(self):
        if self.race is None:
            return "Data Missing"

        for race, label in RACE_CHOICES:
            if self.race == race:
                return label

    def gender_label(self):
        if self.gender is None:
            return "Data Missing"

        for gender, label in GENDER_CHOICES:
            if self.gender == gender:
                return label

    def job_title(self):
        if self.assignments:
            return max(
                self.assignments, key=lambda x: x.start_date or date.min
            ).job.job_title

    def unit_description(self):
        if self.assignments:
            unit = max(self.assignments, key=lambda x: x.start_date or date.min).unit
            return unit.description if unit else None

    def badge_number(self):
        if self.assignments:
            return max(self.assignments, key=lambda x: x.start_date or date.min).star_no

    def currently_on_force(self):
        if self.assignments:
            most_recent = max(self.assignments, key=lambda x: x.start_date or date.min)
            return "Yes" if most_recent.resign_date is None else "No"
        return "Uncertain"

    def __repr__(self):
        if self.unique_internal_identifier:
            return (
                f"<Officer ID {self.id}: {self.full_name()} "
                f"({self.unique_internal_identifier})>"
            )
        return f"<Officer ID {self.id}: {self.full_name()}>"


class Salary(BaseModel, TrackUpdates):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "officers.id", name="salaries_officer_id_fkey", ondelete="CASCADE"
        ),
    )
    officer = db.relationship("Officer", back_populates="salaries")
    salary = db.Column(db.Numeric, index=True, unique=False, nullable=False)
    overtime_pay = db.Column(db.Numeric, index=True, unique=False, nullable=True)
    year = db.Column(db.Integer, index=True, unique=False, nullable=False)
    is_fiscal_year = db.Column(db.Boolean, index=False, unique=False, nullable=False)

    def __repr__(self):
        return f"<Salary: ID {self.officer_id} : {self.salary}"


class Assignment(BaseModel, TrackUpdates):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "officers.id", name="assignments_officer_id_fkey", ondelete="CASCADE"
        ),
    )
    base_officer = db.relationship("Officer", back_populates="assignments")
    star_no = db.Column(db.String(120), index=True, unique=False, nullable=True)
    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id", name="assignments_job_id_fkey"),
        nullable=False,
    )
    job = db.relationship("Job")
    unit_id = db.Column(
        db.Integer,
        db.ForeignKey("unit_types.id", name="assignments_unit_id_fkey"),
        nullable=True,
    )
    unit = db.relationship("Unit")
    start_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    resign_date = db.Column(db.Date, index=True, unique=False, nullable=True)

    def __repr__(self):
        return f"<Assignment: ID {self.officer_id} : {self.star_no}>"


class Unit(BaseModel, TrackUpdates):
    __tablename__ = "unit_types"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), index=True, unique=False)
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", name="unit_types_department_id_fkey"),
    )
    department = db.relationship(
        "Department", backref="unit_types", order_by="Unit.description.asc()"
    )

    def __repr__(self):
        return f"Unit: {self.description}"


class Face(BaseModel, TrackUpdates):
    __tablename__ = "faces"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(
        db.Integer, db.ForeignKey("officers.id", name="faces_officer_id_fkey")
    )
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
    featured = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (UniqueConstraint("officer_id", "img_id", name="unique_faces"),)

    def __repr__(self):
        return f"<Tag ID {self.id}: {self.officer_id} - {self.img_id}>"


class Image(BaseModel, TrackUpdates):
    __tablename__ = "raw_images"

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(255), unique=False)
    hash_img = db.Column(db.String(120), unique=False, nullable=True)

    # We might know when the image was taken e.g. through EXIF data
    taken_at = db.Column(
        db.DateTime(timezone=True), index=True, unique=False, nullable=True
    )
    contains_cops = db.Column(db.Boolean, nullable=True)

    is_tagged = db.Column(db.Boolean, default=False, unique=False, nullable=True)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", name="raw_images_department_id_fkey"),
    )
    department = db.relationship("Department", backref="raw_images")

    def __repr__(self):
        return f"<Image ID {self.id}: {self.filepath}>"


incident_links = db.Table(
    "incident_links",
    db.Column(
        "incident_id",
        db.Integer,
        db.ForeignKey("incidents.id", name="incident_links_incident_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "link_id",
        db.Integer,
        db.ForeignKey("links.id", name="incident_links_link_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)

incident_license_plates = db.Table(
    "incident_license_plates",
    db.Column(
        "incident_id",
        db.Integer,
        db.ForeignKey("incidents.id", name="incident_license_plates_incident_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "license_plate_id",
        db.Integer,
        db.ForeignKey(
            "license_plates.id", name="incident_license_plates_license_plate_id_fkey"
        ),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)

incident_officers = db.Table(
    "incident_officers",
    db.Column(
        "incident_id",
        db.Integer,
        db.ForeignKey("incidents.id", name="incident_officers_incident_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "officers_id",
        db.Integer,
        db.ForeignKey("officers.id", name="incident_officers_officers_id_fkey"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)


class Location(BaseModel, TrackUpdates):
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
            return (
                f"Intersection of {self.street_name} and {self.cross_street2}, "
                + f"{self.city} {self.state}"
            )
        elif self.street_name and self.cross_street1:
            return (
                f"Intersection of {self.street_name} and {self.cross_street1}, "
                + f"{self.city} {self.state}"
            )
        elif self.street_name and self.cross_street1 and self.cross_street2:
            return (
                f"Intersection of {self.street_name} between {self.cross_street1} "
                f"and {self.cross_street2}, {self.city} {self.state}"
            )
        else:
            return f"{self.city} {self.state}"


class LicensePlate(BaseModel, TrackUpdates):
    __tablename__ = "license_plates"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(8), nullable=False, index=True)
    state = db.Column(db.String(2), index=True)

    # for use if car is federal, diplomat, or other non-state
    # non_state_identifier = db.Column(db.String(20), index=True)

    @validates("state")
    def validate_state(self, key, state):
        return state_validator(state)


class Link(BaseModel, TrackUpdates):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), index=True)
    url = db.Column(db.Text(), nullable=False)
    link_type = db.Column(db.String(100), index=True)
    description = db.Column(db.Text(), nullable=True)
    author = db.Column(db.String(255), nullable=True)

    @validates("url")
    def validate_url(self, key, url):
        return url_validator(url)


class Incident(BaseModel, TrackUpdates):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, index=True)
    time = db.Column(db.Time, unique=False, index=True)
    report_number = db.Column(db.String(50), index=True)
    description = db.Column(db.Text(), nullable=True)
    address_id = db.Column(
        db.Integer, db.ForeignKey("locations.id", name="incidents_address_id_fkey")
    )
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
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", name="incidents_department_id_fkey")
    )
    department = db.relationship("Department", backref="incidents", lazy=True)


class User(UserMixin, BaseModel):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)

    # A universally unique identifier (UUID) that can be
    # used in place of the user's primary key for things like user
    # lookup queries.
    _uuid = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    is_area_coordinator = db.Column(db.Boolean, default=False)
    ac_department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", name="users_ac_department_id_fkey")
    )
    ac_department = db.relationship(
        "Department", backref="coordinators", foreign_keys=[ac_department_id]
    )
    is_administrator = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)
    dept_pref = db.Column(
        db.Integer, db.ForeignKey("departments.id", name="users_dept_pref_fkey")
    )
    dept_pref_rel = db.relationship("Department", foreign_keys=[dept_pref])

    # creator backlinks
    classifications = db.relationship(
        "Image", back_populates=KEY_DB_CREATOR, foreign_keys="Image.created_by"
    )
    descriptions = db.relationship(
        "Description",
        back_populates=KEY_DB_CREATOR,
        foreign_keys="Description.created_by",
    )
    incidents_created = db.relationship(
        "Incident", back_populates=KEY_DB_CREATOR, foreign_keys="Incident.created_by"
    )
    links = db.relationship(
        "Link", back_populates=KEY_DB_CREATOR, foreign_keys="Link.created_by"
    )
    notes = db.relationship(
        "Note", back_populates=KEY_DB_CREATOR, foreign_keys="Note.created_by"
    )
    tags = db.relationship(
        "Face", back_populates=KEY_DB_CREATOR, foreign_keys="Face.created_by"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    def _jwt_encode(self, payload, expiration):
        secret = current_app.config["SECRET_KEY"]
        header = {"alg": SIGNATURE_ALGORITHM}

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

    @property
    def uuid(self):
        return self._uuid

    # mypy has difficulty with mixins, specifically the ones where we define a function
    # twice.
    @password.setter  # type: ignore
    def password(self, password):  # type: ignore
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        self.regenerate_uuid()

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
        payload = {"confirm": self.uuid}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def confirm(self, token):
        try:
            data = self._jwt_decode(token)
        except JoseError as e:
            current_app.logger.warning("failed to decrypt token: %s", e)
            return False
        if data.get("confirm") != self.uuid:
            current_app.logger.warning(
                "incorrect uuid here, expected %s, got %s",
                data.get("confirm"),
                self.uuid,
            )
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_reset_token(self, expiration=3600):
        payload = {"reset": self.uuid}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def reset_password(self, token, new_password):
        try:
            data = self._jwt_decode(token)
        except JoseError:
            return False
        if data.get("reset") != self.uuid:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        payload = {"change_email": self.uuid, "new_email": new_email}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def change_email(self, token):
        try:
            data = self._jwt_decode(token)
        except JoseError:
            return False
        if data.get("change_email") != self.uuid:
            return False
        new_email = data.get("new_email")
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.regenerate_uuid()
        db.session.add(self)
        db.session.commit()
        return True

    def regenerate_uuid(self):
        self._uuid = str(uuid.uuid4())

    @property
    def is_active(self):
        """Override UserMixin.is_active to prevent disabled users from logging in."""
        return not self.is_disabled

    def __repr__(self):
        return f"<User {self.username!r}>"
