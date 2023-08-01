import re
import time
from datetime import date

from authlib.jose import JoseError, JsonWebToken
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import validates
from sqlalchemy.sql import func as sql_func
from werkzeug.security import check_password_hash, generate_password_hash

from OpenOversight.app.utils.constants import (
    ENCODING_UTF_8,
    HOUR,
    KEY_TOTAL_ASSIGNMENTS,
    KEY_TOTAL_INCIDENTS,
    KEY_TOTAL_OFFICERS,
)
from OpenOversight.app.validators import state_validator, url_validator


db = SQLAlchemy()
jwt = JsonWebToken("HS512")

BaseModel = db.Model  # type: DefaultMeta

officer_links = db.Table(
    "officer_links",
    db.Column("officer_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True),
    db.Column("link_id", db.Integer, db.ForeignKey("links.id"), primary_key=True),
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
    db.Column("officer_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True),
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    ),
)

# This is a last recently used cache that also utilizes a time-to-live function for each
# value saved in it (12 hours).
# TODO: Change this into a singleton so that we can clear values when updates happen
DATABASE_CACHE = TTLCache(maxsize=1024, ttl=12 * HOUR)


# TODO: In the singleton create functions for other model types.
def _date_updated_cache_key(update_type: str):
    """Return a key function to calculate the cache key for Department
    methods using the department id and a given update type.

    Department.id is used instead of a Department obj because the default Python
    __hash__ is unique per obj instance, meaning multiple instances of the same
    department will have different hashes.

    Update type is used in the hash to differentiate between the update types we compute
    per department.
    """

    def _cache_key(dept: "Department"):
        return hashkey(dept.id, update_type)

    return _cache_key


class Department(BaseModel):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=False, unique=False, nullable=False)
    short_name = db.Column(db.String(100), unique=False, nullable=False)
    state = db.Column(db.String(2), server_default="", nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

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

    @cached(cache=DATABASE_CACHE, key=_date_updated_cache_key(KEY_TOTAL_ASSIGNMENTS))
    def total_documented_assignments(self):
        return (
            db.session.query(Assignment.id)
            .join(Officer, Assignment.officer_id == Officer.id)
            .filter(Officer.department_id == self.id)
            .count()
        )

    @cached(cache=DATABASE_CACHE, key=_date_updated_cache_key(KEY_TOTAL_INCIDENTS))
    def total_documented_incidents(self):
        return (
            db.session.query(Incident).filter(Incident.department_id == self.id).count()
        )

    @cached(cache=DATABASE_CACHE, key=_date_updated_cache_key(KEY_TOTAL_OFFICERS))
    def total_documented_officers(self):
        return (
            db.session.query(Officer).filter(Officer.department_id == self.id).count()
        )


class Job(BaseModel):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), index=True, unique=False, nullable=False)
    is_sworn_officer = db.Column(db.Boolean, index=True, default=True)
    order = db.Column(db.Integer, index=True, unique=False, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="jobs")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "job_title", "department_id", name="unique_department_job_titles"
        ),
    )

    def __repr__(self):
        return f"<Job ID {self.id,}: {self.job_title}>"

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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )
    updated_at = db.Column(db.DateTime(timezone=True), unique=False)


class Description(BaseModel):
    __tablename__ = "descriptions"

    creator = db.relationship("User", backref="descriptions")
    officer = db.relationship("Officer", back_populates="descriptions")
    id = db.Column(db.Integer, primary_key=True)
    text_contents = db.Column(db.Text())
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )
    updated_at = db.Column(db.DateTime(timezone=True), unique=False)


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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
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
        from OpenOversight.app.main.choices import RACE_CHOICES

        for race, label in RACE_CHOICES:
            if self.race == race:
                return label

    def gender_label(self):
        if self.gender is None:
            return "Data Missing"
        from OpenOversight.app.main.choices import GENDER_CHOICES

        for gender, label in GENDER_CHOICES:
            if self.gender == gender:
                return label

    def job_title(self):
        if self.assignments_lazy:
            return max(
                self.assignments_lazy, key=lambda x: x.start_date or date.min
            ).job.job_title

    def unit_description(self):
        if self.assignments_lazy:
            unit = max(
                self.assignments_lazy, key=lambda x: x.start_date or date.min
            ).unit
            return unit.description if unit else None

    def badge_number(self):
        if self.assignments_lazy:
            return max(
                self.assignments_lazy, key=lambda x: x.start_date or date.min
            ).star_no

    def currently_on_force(self):
        if self.assignments_lazy:
            most_recent = max(
                self.assignments_lazy, key=lambda x: x.start_date or date.min
            )
            return "Yes" if most_recent.resign_date is None else "No"
        return "Uncertain"

    def __repr__(self):
        if self.unique_internal_identifier:
            return (
                f"<Officer ID {self.id}: {self.first_name} {self.middle_initial} "
                + f"{self.last_name} {self.suffix} ({self.unique_internal_identifier})>"
            )
        return (
            f"<Officer ID {self.id}: {self.first_name} {self.middle_initial} "
            + f"{self.last_name} {self.suffix}>"
        )


class Salary(BaseModel):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id", ondelete="CASCADE"))
    officer = db.relationship("Officer", back_populates="salaries")
    salary = db.Column(db.Numeric, index=True, unique=False, nullable=False)
    overtime_pay = db.Column(db.Numeric, index=True, unique=False, nullable=True)
    year = db.Column(db.Integer, index=True, unique=False, nullable=False)
    is_fiscal_year = db.Column(db.Boolean, index=False, unique=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    def __repr__(self):
        return f"<Salary: ID {self.officer_id} : {self.salary}"


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
    start_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    resign_date = db.Column(db.Date, index=True, unique=False, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    def __repr__(self):
        return f"<Assignment: ID {self.officer_id} : {self.star_no}>"


class Unit(BaseModel):
    __tablename__ = "unit_types"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), index=True, unique=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship(
        "Department", backref="unit_types", order_by="Unit.description.asc()"
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    def __repr__(self):
        return f"Unit: {self.description}"


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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

    __table_args__ = (UniqueConstraint("officer_id", "img_id", name="unique_faces"),)

    def __repr__(self):
        return f"<Tag ID {self.id}: {self.officer_id} - {self.img_id}>"


class Image(BaseModel):
    __tablename__ = "raw_images"

    id = db.Column(db.Integer, primary_key=True)
    filepath = db.Column(db.String(255), unique=False)
    hash_img = db.Column(db.String(120), unique=False, nullable=True)

    # Track when the image was put into our database
    created_at = db.Column(
        db.DateTime(timezone=True),
        index=True,
        unique=False,
        server_default=sql_func.now(),
    )

    # We might know when the image was taken e.g. through EXIF data
    taken_at = db.Column(
        db.DateTime(timezone=True), index=True, unique=False, nullable=True
    )
    contains_cops = db.Column(db.Boolean, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", backref="raw_images")
    is_tagged = db.Column(db.Boolean, default=False, unique=False, nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", backref="raw_images")

    def __repr__(self):
        return f"<Image ID {self.id}: {self.filepath}>"


incident_links = db.Table(
    "incident_links",
    db.Column(
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column("link_id", db.Integer, db.ForeignKey("links.id"), primary_key=True),
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
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column(
        "license_plate_id",
        db.Integer,
        db.ForeignKey("license_plates.id"),
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
        "incident_id", db.Integer, db.ForeignKey("incidents.id"), primary_key=True
    ),
    db.Column(
        "officers_id", db.Integer, db.ForeignKey("officers.id"), primary_key=True
    ),
    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

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


class LicensePlate(BaseModel):
    __tablename__ = "license_plates"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(8), nullable=False, index=True)
    state = db.Column(db.String(2), index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
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
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now(),
        unique=False,
    )

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
        return f"<User {self.username!r}>"
