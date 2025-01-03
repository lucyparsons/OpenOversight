import operator
import re
import time
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from authlib.jose import JoseError, JsonWebToken
from cachetools import cached
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    backref,
    declarative_mixin,
    declared_attr,
    mapped_column,
    relationship,
    validates,
)
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


class BaseModel(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""


officer_links = db.Table(
    "officer_links",
    Column(
        "officer_id",
        Integer,
        ForeignKey("officers.id", name="officer_links_officer_id_fkey"),
        primary_key=True,
    ),
    Column(
        "link_id",
        Integer,
        ForeignKey("links.id", name="officer_links_link_id_fkey"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        unique=False,
    ),
)

officer_incidents = db.Table(
    "officer_incidents",
    Column(
        "officer_id",
        Integer,
        ForeignKey("officers.id", name="officer_incidents_officer_id_fkey"),
        primary_key=True,
    ),
    Column(
        "incident_id",
        Integer,
        ForeignKey("incidents.id", name="officer_incidents_incident_id_fkey"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
        server_default=func.now(),
        unique=False,
    )
    last_updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        unique=False,
    )

    @declared_attr
    def created_by(cls):
        return db.Column(
            db.Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            unique=False,
        )

    @declared_attr
    def last_updated_by(cls):
        return db.Column(
            db.Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            unique=False,
        )

    @declared_attr
    def creator(cls):
        return relationship(
            "User", foreign_keys=[cls.created_by], backref="created_objects"
        )

    @declared_attr
    def last_updater(cls):
        return relationship(
            "User", foreign_keys=[cls.last_updated_by], backref="updated_objects"
        )


class Department(BaseModel, TrackUpdates):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), server_default="", nullable=False)

    unique_internal_identifier_label: Mapped[str] = mapped_column(
        String(100), nullable=True
    )

    __table_args__ = (UniqueConstraint("name", "state", name="departments_name_state"),)

    def to_custom_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "state": self.state,
            "unique_internal_identifier_label": self.unique_internal_identifier_label,
        }

    @property
    def display_name(self) -> str:
        return self.name if not self.state else f"[{self.state}] {self.name}"

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_ASSIGNMENTS))
    def total_documented_assignments(self) -> int:
        return (
            self.db_session.query(Assignment.id)
            .join(Officer, Assignment.officer_id == Officer.id)
            .filter(Officer.department_id == self.id)
            .count()
        )

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_INCIDENTS))
    def total_documented_incidents(self) -> int:
        return (
            self.db_session.query(Incident)
            .filter(Incident.department_id == self.id)
            .count()
        )

    @cached(cache=DB_CACHE, key=model_cache_key(KEY_DEPT_TOTAL_OFFICERS))
    def total_documented_officers(self) -> int:
        return (
            self.db_session.query(Officer)
            .filter(Officer.department_id == self.id)
            .count()
        )

    def remove_database_cache_entries(self, update_types: List[str]) -> None:
        """Remove the Department model key from the cache if it exists."""
        remove_database_cache_entries(self, update_types)


class Job(BaseModel, TrackUpdates):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    is_sworn_officer: Mapped[bool] = mapped_column(Boolean, index=True, default=True)
    order: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", name="jobs_department_id_fkey")
    )
    department: Mapped["Department"] = relationship(
        "Department",
        backref=backref("jobs", cascade_backrefs=False),
    )

    __table_args__ = (
        UniqueConstraint(
            "job_title", "department_id", name="unique_department_job_titles"
        ),
    )


class Note(BaseModel, TrackUpdates):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text_contents: Mapped[str] = mapped_column(Text, nullable=True)
    officer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("officers.id", ondelete="CASCADE")
    )
    officer: Mapped["Officer"] = relationship("Officer", back_populates="notes")


class Description(BaseModel, TrackUpdates):
    __tablename__ = "descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text_contents: Mapped[str] = mapped_column(Text, nullable=True)
    officer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("officers.id", ondelete="CASCADE")
    )
    officer: Mapped["Officer"] = relationship("Officer", back_populates="descriptions")


class Officer(BaseModel, TrackUpdates):
    __tablename__ = "officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column(String(120), index=True)
    first_name: Mapped[str] = mapped_column(String(120), index=True)
    middle_initial: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(
        String(120), index=True, nullable=True
    )
    race: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(5), index=True, nullable=True)
    employment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", name="officers_department_id_fkey")
    )
    department: Mapped["Department"] = relationship(
        "Department", backref="officers", cascade_backrefs=False
    )
    unique_internal_identifier: Mapped[Optional[str]] = mapped_column(
        String(50), index=True, unique=True, nullable=True
    )

    # Relationships
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment", back_populates="base_officer"
    )
    face: Mapped[list["Face"]] = relationship(
        "Face", backref="officer", cascade_backrefs=False
    )
    links: Mapped[list["Link"]] = relationship(
        "Link", secondary=officer_links, backref="officers", lazy=True
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="officer", order_by="Note.created_at"
    )
    descriptions: Mapped[list["Description"]] = relationship(
        "Description", back_populates="officer", order_by="Description.created_at"
    )
    salaries: Mapped[list["Salary"]] = relationship(
        "Salary", back_populates="officer", order_by="Salary.year.desc()"
    )

    __table_args__ = (
        CheckConstraint("gender in ('M', 'F', 'Other')", name="gender_options"),
    )

    def full_name(self) -> str:
        if self.middle_initial:
            middle_initial = (
                self.middle_initial + "."
                if len(self.middle_initial) == 1
                else self.middle_initial
            )
            return (
                f"{self.first_name} {middle_initial} {self.last_name} {self.suffix}"
                if self.suffix
                else f"{self.first_name} {middle_initial} {self.last_name}"
            )
        return (
            f"{self.first_name} {self.last_name} {self.suffix}"
            if self.suffix
            else f"{self.first_name} {self.last_name}"
        )

    def race_label(self) -> str:
        for race, label in RACE_CHOICES:
            if self.race == race:
                return label
        return "Data Missing"

    def gender_label(self) -> str:
        for gender, label in GENDER_CHOICES:
            if self.gender == gender:
                return label
        return "Data Missing"

    def job_title(self) -> Optional[str]:
        return (
            max(
                self.assignments, key=operator.attrgetter("start_date_or_min")
            ).job.job_title
            if self.assignments
            else None
        )

    def unit_description(self) -> Optional[str]:
        return (
            max(
                self.assignments, key=operator.attrgetter("start_date_or_min")
            ).unit.description
            if self.assignments
            else None
        )

    def badge_number(self) -> Optional[str]:
        return (
            max(self.assignments, key=operator.attrgetter("start_date_or_min")).star_no
            if self.assignments
            else None
        )

    def currently_on_force(self) -> str:
        most_recent = (
            max(self.assignments, key=operator.attrgetter("start_date_or_min"))
            if self.assignments
            else None
        )
        return (
            "Yes"
            if most_recent and most_recent.resign_date is None
            else "No"
            if most_recent
            else "Uncertain"
        )


class Salary(BaseModel, TrackUpdates):
    __tablename__ = "salaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    officer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("officers.id", name="salaries_officer_id_fkey", ondelete="CASCADE"),
    )
    officer: Mapped["Officer"] = relationship("Officer", back_populates="salaries")
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    overtime_pay: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_fiscal_year: Mapped[bool] = mapped_column(Boolean, nullable=False)

    @property
    def total_pay(self) -> float:
        return self.salary + (self.overtime_pay or 0)

    @property
    def year_repr(self) -> str:
        return f"FY{self.year}" if self.is_fiscal_year else str(self.year)


class Assignment(BaseModel, TrackUpdates):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    officer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "officers.id", name="assignments_officer_id_fkey", ondelete="CASCADE"
        ),
    )
    base_officer: Mapped["Officer"] = relationship(
        "Officer", back_populates="assignments"
    )
    star_no: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", name="assignments_job_id_fkey"), nullable=False
    )
    job: Mapped["Job"] = relationship("Job")
    unit_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("unit_types.id", name="assignments_unit_id_fkey"),
        nullable=True,
    )
    unit: Mapped["Unit"] = relationship("Unit")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resign_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    @property
    def start_date_or_min(self) -> date:
        return self.start_date or date.min

    @property
    def start_date_or_max(self) -> date:
        return self.start_date or date.max


class Unit(BaseModel, TrackUpdates):
    __tablename__ = "unit_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(120), index=True, nullable=True)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", name="unit_types_department_id_fkey")
    )
    department: Mapped["Department"] = relationship(
        "Department",
        backref="unit_types",
        cascade_backrefs=False,
        order_by="Unit.description.asc()",
    )


class Face(BaseModel, TrackUpdates):
    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    officer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("officers.id", name="faces_officer_id_fkey")
    )
    img_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "raw_images.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="fk_face_image_id",
            use_alter=True,
        ),
    )
    original_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "raw_images.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
            use_alter=True,
            name="fk_face_original_image_id",
        ),
    )
    face_position_x: Mapped[int] = mapped_column(Integer, unique=False)
    face_position_y: Mapped[int] = mapped_column(Integer, unique=False)
    face_width: Mapped[int] = mapped_column(Integer, unique=False)
    face_height: Mapped[int] = mapped_column(Integer, unique=False)
    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    image: Mapped["Image"] = relationship(
        "Image",
        backref="faces",
        cascade_backrefs=False,
        foreign_keys=[img_id],
    )
    original_image: Mapped["Image"] = relationship(
        "Image",
        backref="tags",
        cascade_backrefs=False,
        foreign_keys=[original_image_id],
        lazy=True,
    )

    __table_args__ = (UniqueConstraint("officer_id", "img_id", name="unique_faces"),)


class Image(BaseModel, TrackUpdates):
    __tablename__ = "raw_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filepath: Mapped[str] = mapped_column(String(255), unique=False)
    hash_img: Mapped[str] = mapped_column(String(120), unique=False, nullable=True)

    # We might know when the image was taken e.g. through EXIF data
    taken_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), index=True, unique=False, nullable=True
    )
    contains_cops: Mapped[bool] = mapped_column(Boolean, nullable=True)

    is_tagged: Mapped[bool] = mapped_column(
        Boolean, default=False, unique=False, nullable=True
    )

    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", name="raw_images_department_id_fkey"),
    )
    department: Mapped["Department"] = relationship(
        "Department", backref="raw_images", cascade_backrefs=False
    )


incident_links = db.Table(
    "incident_links",
    mapped_column(
        "incident_id",
        Integer,
        ForeignKey("incidents.id", name="incident_links_incident_id_fkey"),
        primary_key=True,
    ),
    mapped_column(
        "link_id",
        Integer,
        ForeignKey("links.id", name="incident_links_link_id_fkey"),
        primary_key=True,
    ),
    mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

incident_license_plates = db.Table(
    "incident_license_plates",
    mapped_column(
        "incident_id",
        Integer,
        ForeignKey("incidents.id", name="incident_license_plates_incident_id_fkey"),
        primary_key=True,
    ),
    mapped_column(
        "license_plate_id",
        Integer,
        ForeignKey(
            "license_plates.id", name="incident_license_plates_license_plate_id_fkey"
        ),
        primary_key=True,
    ),
    mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

incident_officers = db.Table(
    "incident_officers",
    mapped_column(
        "incident_id",
        Integer,
        ForeignKey("incidents.id", name="incident_officers_incident_id_fkey"),
        primary_key=True,
    ),
    mapped_column(
        "officers_id",
        Integer,
        ForeignKey("officers.id", name="incident_officers_officers_id_fkey"),
        primary_key=True,
    ),
    mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)


class Location(BaseModel, TrackUpdates):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    street_name: Mapped[str] = mapped_column(String(100), index=True)
    cross_street1: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cross_street2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(2), index=True)
    zip_code: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)

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
        if self.street_name and self.cross_street1 and self.cross_street2:
            return (
                f"Intersection of {self.street_name} between {self.cross_street1} "
                f"and {self.cross_street2}, {self.city} {self.state}"
            )
        elif self.street_name and self.cross_street2:
            return (
                f"Intersection of {self.street_name} and {self.cross_street2}, "
                f"{self.city} {self.state}"
            )
        elif self.street_name and self.cross_street1:
            return (
                f"Intersection of {self.street_name} and {self.cross_street1}, "
                f"{self.city} {self.state}"
            )
        else:
            return f"{self.city} {self.state}"


class LicensePlate(BaseModel, TrackUpdates):
    __tablename__ = "license_plates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True)

    # for use if car is federal, diplomat, or other non-state
    # non_state_identifier: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    @validates("state")
    def validate_state(self, key, state):
        return state_validator(state)


class Link(BaseModel, TrackUpdates):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(100), index=True)
    url: Mapped[str] = mapped_column(Text(), nullable=False)
    link_type: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_content_warning: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    @validates("url")
    def validate_url(self, key, url):
        return url_validator(url)


class Incident(BaseModel, TrackUpdates):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date | None] = mapped_column(Date, index=True)
    time: Mapped[time | None] = mapped_column(Time, index=True)
    report_number: Mapped[str | None] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    address_id: Mapped[int | None] = mapped_column(
        Integer, db.ForeignKey("locations.id", name="incidents_address_id_fkey")
    )
    address: Mapped["Location"] = relationship(
        "Location", backref=db.backref("incidents", cascade_backrefs=False)
    )

    license_plates: Mapped[list["LicensePlate"]] = relationship(
        "LicensePlate",
        secondary=incident_license_plates,
        lazy="subquery",
        backref=db.backref("incidents", cascade_backrefs=False, lazy=True),
    )

    links: Mapped[list["Link"]] = relationship(
        "Link",
        secondary=incident_links,
        lazy="subquery",
        backref=db.backref("incidents", cascade_backrefs=False, lazy=True),
    )

    officers: Mapped[list["Officer"]] = relationship(
        "Officer",
        secondary=incident_officers,
        lazy="subquery",
        backref=db.backref(
            "incidents",
            cascade_backrefs=False,
            order_by="Incident.date.desc(), Incident.time.desc()",
        ),
    )

    department_id: Mapped[int | None] = mapped_column(
        Integer, db.ForeignKey("departments.id", name="incidents_department_id_fkey")
    )
    department: Mapped["Department"] = relationship(
        "Department", backref=db.backref("incidents", cascade_backrefs=False), lazy=True
    )


class User(UserMixin, BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    _uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(128))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", name="users_confirmed_by_fkey"),
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", name="users_approved_by_fkey"),
    )
    is_area_coordinator: Mapped[bool] = mapped_column(Boolean, default=False)
    ac_department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", name="users_ac_department_id_fkey")
    )
    ac_department: Mapped["Department"] = relationship(
        "Department",
        backref=db.backref("coordinators", cascade_backrefs=False),
        foreign_keys=[ac_department_id],
    )
    is_administrator: Mapped[bool] = mapped_column(Boolean, default=False)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", name="users_disabled_by_fkey"),
    )

    dept_pref: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", name="users_dept_pref_fkey")
    )
    dept_pref_rel: Mapped["Department"] = relationship(
        "Department", foreign_keys=[dept_pref]
    )

    # creator backlinks
    classifications: Mapped[list["Image"]] = relationship(
        "Image", back_populates=KEY_DB_CREATOR, foreign_keys="Image.created_by"
    )
    descriptions: Mapped[list["Description"]] = relationship(
        "Description",
        back_populates=KEY_DB_CREATOR,
        foreign_keys="Description.created_by",
    )
    incidents_created: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates=KEY_DB_CREATOR, foreign_keys="Incident.created_by"
    )
    links: Mapped[list["Link"]] = relationship(
        "Link", back_populates=KEY_DB_CREATOR, foreign_keys="Link.created_by"
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates=KEY_DB_CREATOR, foreign_keys="Note.created_by"
    )
    tags: Mapped[list["Face"]] = relationship(
        "Face", back_populates=KEY_DB_CREATOR, foreign_keys="Face.created_by"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        unique=False,
    )

    __table_args__ = (
        CheckConstraint(
            "(disabled_at IS NULL and disabled_by IS NULL) or (disabled_at IS NOT NULL and disabled_by IS NOT NULL)",
            name="users_disabled_constraint",
        ),
        CheckConstraint(
            "(confirmed_at IS NULL and confirmed_by IS NULL) or (confirmed_at IS NOT NULL and confirmed_by IS NOT NULL)",
            name="users_confirmed_constraint",
        ),
        CheckConstraint(
            "(approved_at IS NULL and approved_by IS NULL) or (approved_at IS NOT NULL and approved_by IS NOT NULL)",
            name="users_approved_constraint",
        ),
    )

    def is_admin_or_coordinator(self, department: Optional["Department"]) -> bool:
        return self.is_administrator or (
            department is not None
            and (self.is_area_coordinator and self.ac_department_id == department.id)
        )

    def _jwt_encode(self, payload, expiration: int) -> str:
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

    @password.setter  # type: ignore
    def password(self, password: str) -> None:  # type: ignore
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        self.regenerate_uuid()

    @property
    def uuid(self) -> str:
        return self._uuid

    @staticmethod
    def _case_insensitive_equality(field, value: str):
        return User.query.filter(func.lower(field) == func.lower(value))

    @staticmethod
    def by_email(email: str):
        return User._case_insensitive_equality(User.email, email)

    @staticmethod
    def by_username(username: str):
        return User._case_insensitive_equality(User.username, username)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        payload = {"confirm": self.uuid}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def confirm(self, token: str, confirming_user_id: int) -> bool:
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
        self.confirmed_at = datetime.now(timezone.utc)
        self.confirmed_by = confirming_user_id
        self.db_session.add(self)
        self.db_session.commit()
        return True

    def generate_reset_token(self, expiration=3600):
        payload = {"reset": self.uuid}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def reset_password(self, token: str, new_password: str) -> bool:
        try:
            data = self._jwt_decode(token)
        except JoseError:
            return False
        if data.get("reset") != self.uuid:
            return False
        self.password = new_password
        self.db_session.add(self)
        self.db_session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        payload = {"change_email": self.uuid, "new_email": new_email}
        return self._jwt_encode(payload, expiration).decode(ENCODING_UTF_8)

    def change_email(self, token: str) -> bool:
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
        self.db_session.add(self)
        self.db_session.commit()
        return True

    def regenerate_uuid(self) -> None:
        self._uuid = str(uuid.uuid4())

    def get_id(self) -> str:
        """Get the Flask-Login user identifier, NOT THE DATABASE ID."""
        return str(self.uuid)

    @property
    def is_active(self) -> bool:
        """Override UserMixin.is_active to prevent disabled users from logging in."""
        return not self.disabled_at

    def approve_user(self, approving_user_id: int) -> bool:
        """Handle approving logic."""
        if self.approved_at or self.approved_by:
            return False

        self.approved_at = datetime.now(timezone.utc)
        self.approved_by = approving_user_id
        self.db_session.add(self)
        self.db_session.commit()
        return True

    def confirm_user(self, confirming_user_id: int) -> bool:
        """Handle confirming logic."""
        if self.confirmed_at or self.confirmed_by:
            return False

        self.confirmed_at = datetime.now(timezone.utc)
        self.confirmed_by = confirming_user_id
        self.db_session.add(self)
        self.db_session.commit()
        return True

    def disable_user(self, disabling_user_id: int) -> bool:
        """Handle disabling logic."""
        if self.disabled_at or self.disabled_by:
            return False

        self.disabled_at = datetime.now(timezone.utc)
        self.disabled_by = disabling_user_id
        self.db_session.add(self)
        self.db_session.commit()
        return True
