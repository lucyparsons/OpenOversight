import datetime
import random
import time
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from pytest import raises
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from OpenOversight.app.models.database import (
    Assignment,
    Department,
    Image,
    Incident,
    LicensePlate,
    Link,
    Location,
    Officer,
    Salary,
    TZDateTime,
    User,
)
from OpenOversight.app.utils.choices import STATE_CHOICES
from OpenOversight.tests.conftest import AC_DEPT, SPRINGFIELD_PD


def test_no_omitted_fields_in_to_dict(mockdata):
    department_dict = Department.query.filter_by(id=AC_DEPT).first().to_dict()

    assert "created_by" not in department_dict.keys()
    assert "last_updated_at" not in department_dict.keys()


def test_department_by_state(mockdata, session, faker):
    department = Department(
        name="Peoria Police Department",
        short_name="PPD",
        state="IL",
        unique_internal_identifier_label="UID",
        created_by=1,
        last_updated_by=1,
    )
    officer = Officer(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        department=department,
    )
    session.add(department)
    session.add(officer)
    session.commit()

    departments_by_state = Department.by_state()

    # expected departments: SPD (IL), CPD (non-IL), PPD (IL)
    assert len(departments_by_state.items()) == 2
    assert len(departments_by_state["IL"]) == 2
    assert {dept.short_name for dept in departments_by_state["IL"]} == {"SPD", "PPD"}


def test_department_total_documented_officers(mockdata):
    springfield_officers = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .join(Officer, Department.id == Officer.department_id)
        .count()
    )

    test_count = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .first()
        .total_documented_officers()
    )

    assert springfield_officers == test_count


def test_department_total_documented_assignments(mockdata):
    springfield_assignments = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .join(Officer, Department.id == Officer.department_id)
        .join(Assignment, Officer.id == Assignment.officer_id)
        .count()
    )

    test_count = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .first()
        .total_documented_assignments()
    )

    assert springfield_assignments == test_count


def test_department_total_documented_incidents(mockdata):
    springfield_incidents = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .join(Incident, Department.id == Incident.department_id)
        .count()
    )

    test_count = (
        Department.query.filter_by(name=SPRINGFIELD_PD.name, state=SPRINGFIELD_PD.state)
        .first()
        .total_documented_incidents()
    )

    assert springfield_incidents == test_count


def test_officer_repr(session):
    officer_uii = Officer.query.filter(
        and_(
            Officer.middle_initial.isnot(None),
            Officer.unique_internal_identifier.isnot(None),
            Officer.suffix.is_(None),
        )
    ).first()

    assert (
        repr(officer_uii) == f"<Officer ID: {officer_uii.id} : "
        f"{officer_uii.first_name} {officer_uii.middle_initial}. {officer_uii.last_name} "
        f"({officer_uii.unique_internal_identifier})>"
    )

    officer_no_uii = Officer.query.filter(
        and_(
            Officer.middle_initial.isnot(""),
            Officer.unique_internal_identifier.is_(None),
            Officer.suffix.isnot(None),
        )
    ).first()

    assert (
        repr(officer_no_uii) == f"<Officer ID: {officer_no_uii.id} : "
        f"{officer_no_uii.first_name} {officer_no_uii.middle_initial}. "
        f"{officer_no_uii.last_name} {officer_no_uii.suffix}>"
    )

    officer_no_mi = Officer.query.filter(
        and_(Officer.middle_initial.is_(""), Officer.suffix.isnot(None))
    ).first()

    assert (
        repr(officer_no_mi)
        == f"<Officer ID: {officer_no_mi.id} : {officer_no_mi.first_name} "
        f"{officer_no_mi.last_name} {officer_no_mi.suffix} "
        f"({officer_no_mi.unique_internal_identifier})>"
    )


def test_officer_race_label(faker):
    officer = Officer(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
    )

    assert officer.race_label() == "Data Missing"


def test_password_not_printed(mockdata):
    """Validate that password fields cannot be directly accessed."""
    user = User(password="bacon")
    with raises(AttributeError):
        print(user.password)


def test_password_set_success(mockdata):
    user = User(password="bacon")
    assert user.password_hash is not None


def test_password_setter_regenerates_uuid(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()
    initial_uuid = user.uuid
    user.password = "pork belly"
    assert user.uuid is not None
    assert user.uuid != initial_uuid


def test_password_verification_success(mockdata):
    user = User(password="bacon")
    assert user.verify_password("bacon") is True


def test_password_verification_failure(mockdata):
    user = User(password="bacon")
    assert user.verify_password("vegan bacon") is False


def test_password_salting(mockdata):
    user1 = User(password="bacon")
    user2 = User(password="bacon")
    assert user1.password_hash != user2.password_hash


def test__uuid_default(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()
    assert user._uuid is not None


def test__uuid_uniqueness_constraint(mockdata, session):
    user1 = User(password="bacon")
    user2 = User(password="vegan bacon")
    user2._uuid = user1._uuid
    session.add(user1)
    session.add(user2)
    with raises(IntegrityError):
        session.commit()


def test_uuid(mockdata):
    user = User(password="bacon")
    assert user.uuid is not None
    assert user.uuid == user._uuid


def test_uuid_setter(mockdata):
    with raises(AttributeError):
        User(uuid="8e9f1393-99b8-466c-80ce-8a56a7d9849d")


def test_valid_confirmation_token(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()

    admin_user = User.query.filter_by(is_administrator=False).first()
    token = user.generate_confirmation_token()

    assert user.confirm(token, admin_user.id) is True


def test_invalid_confirmation_token(mockdata, session):
    user1 = User(password="bacon")
    user2 = User(password="bacon")
    session.add(user1)
    session.add(user2)
    session.commit()

    admin_user = User.query.filter_by(is_administrator=False).first()
    token = user1.generate_confirmation_token()

    assert user2.confirm(token, admin_user.id) is False


def test_expired_confirmation_token(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()

    admin_user = User.query.filter_by(is_administrator=False).first()
    token = user.generate_confirmation_token(1)
    time.sleep(2)

    assert user.confirm(token, admin_user.id) is False


def test_valid_reset_token(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()
    token = user.generate_reset_token()
    pre_reset_uuid = user.uuid
    assert user.reset_password(token, "vegan bacon") is True
    assert user.verify_password("vegan bacon") is True
    assert user.uuid != pre_reset_uuid


def test_invalid_reset_token(mockdata, session):
    user1 = User(password="bacon")
    user2 = User(password="vegan bacon")
    session.add(user1)
    session.add(user2)
    session.commit()
    token = user1.generate_reset_token()
    assert user2.reset_password(token, "tempeh") is False
    assert user2.verify_password("vegan bacon") is True


def test_expired_reset_token(mockdata, session):
    user = User(password="bacon")
    session.add(user)
    session.commit()
    token = user.generate_reset_token(expiration=-1)
    assert user.reset_password(token, "tempeh") is False
    assert user.verify_password("bacon") is True


def test_valid_email_change_token(mockdata, session):
    user = User(email="brian@example.com", password="bacon")
    session.add(user)
    session.commit()
    pre_reset_uuid = user.uuid
    token = user.generate_email_change_token("lucy@example.org")
    assert user.change_email(token) is True
    assert user.email == "lucy@example.org"
    assert user.uuid != pre_reset_uuid


def test_email_change_token_no_email(mockdata, session):
    user = User(email="brian@example.com", password="bacon")
    session.add(user)
    session.commit()
    token = user.generate_email_change_token(None)
    assert user.change_email(token) is False
    assert user.email == "brian@example.com"


def test_invalid_email_change_token(mockdata, session):
    user1 = User(email="jen@example.com", password="cat")
    user2 = User(email="freddy@example.com", password="dog")
    session.add(user1)
    session.add(user2)
    session.commit()
    token = user1.generate_email_change_token("mason@example.net")
    assert user2.change_email(token) is False
    assert user2.email == "freddy@example.com"


def test_expired_email_change_token(mockdata, session):
    user = User(email="jen@example.com", password="cat")
    session.add(user)
    session.commit()
    token = user.generate_email_change_token("mason@example.net", expiration=-1)
    assert user.change_email(token) is False
    assert user.email == "jen@example.com"


def test_duplicate_email_change_token(mockdata, session):
    user1 = User(email="alice@example.com", password="cat")
    user2 = User(email="bob@example.org", password="dog")
    session.add(user1)
    session.add(user2)
    session.commit()
    token = user2.generate_email_change_token("alice@example.com")
    assert user2.change_email(token) is False
    assert user2.email == "bob@example.org"


def test_area_coordinator_with_dept_is_valid(mockdata, session):
    user1 = User(
        email="alice@example.com",
        username="me",
        password="cat",
        is_area_coordinator=True,
        ac_department_id=1,
    )
    session.add(user1)
    session.commit()
    assert user1.is_area_coordinator is True
    assert user1.ac_department_id == 1


def test_locations_must_have_valid_zip_codes(mockdata):
    with raises(ValueError):
        Location(
            street_name="Brookford St",
            cross_street1="Mass Ave",
            cross_street2="None",
            city="Cambridge",
            state="MA",
            zip_code="543",
        )


def test_location_repr(faker):
    street_name = faker.street_address()
    cross_street_one = faker.street_name()
    cross_street_two = faker.street_name()
    state = random.choice(STATE_CHOICES)[0]
    city = faker.city()
    zip_code = faker.postcode()

    no_cross_streets = Location(
        street_name=street_name,
        state=state,
        city=city,
        zip_code=zip_code,
    )

    assert repr(no_cross_streets) == f"{city} {state}"

    cross_street1 = Location(
        street_name=street_name,
        cross_street1=cross_street_one,
        state=state,
        city=city,
        zip_code=zip_code,
    )

    assert (
        repr(cross_street1)
        == f"Intersection of {street_name} and {cross_street_one}, {city} {state}"
    )

    cross_street2 = Location(
        street_name=street_name,
        cross_street2=cross_street_two,
        state=state,
        city=city,
        zip_code=zip_code,
    )

    assert (
        repr(cross_street2)
        == f"Intersection of {street_name} and {cross_street_two}, {city} {state}"
    )

    both_cross_streets = Location(
        street_name=street_name,
        cross_street1=cross_street_one,
        cross_street2=cross_street_two,
        state=state,
        city=city,
        zip_code=zip_code,
    )

    assert repr(both_cross_streets) == (
        f"Intersection of {street_name} between {cross_street_one} and "
        f"{cross_street_two}, {city} {state}"
    )


def test_locations_can_be_saved_with_valid_zip_codes(mockdata, session):
    zip_code = "03456"
    city = "Cambridge"
    lo = Location(
        street_name="Brookford St",
        cross_street1="Mass Ave",
        cross_street2="None",
        city=city,
        state="MA",
        zip_code=zip_code,
    )
    session.add(lo)
    session.commit()
    saved = Location.query.filter_by(zip_code=zip_code, city=city)
    assert saved is not None


def test_locations_must_have_valid_states(mockdata):
    with raises(ValueError):
        Location(
            street_name="Brookford St",
            cross_street1="Mass Ave",
            cross_street2="None",
            city="Cambridge",
            state="JK",
            zip_code="54340",
        )


def test_locations_can_be_saved_with_valid_states(mockdata, session):
    state = "AZ"
    city = "Cambridge"
    lo = Location(
        street_name="Brookford St",
        cross_street1="Mass Ave",
        cross_street2="None",
        city=city,
        state=state,
        zip_code="54340",
    )

    session.add(lo)
    session.commit()
    saved = Location.query.filter_by(city=city, state=state).first()
    assert saved is not None


def test_license_plates_must_have_valid_states(mockdata):
    with raises(ValueError):
        LicensePlate(number="603EEE", state="JK")


def test_license_plates_can_be_saved_with_valid_states(mockdata, session):
    state = "AZ"
    number = "603RRR"
    lp = LicensePlate(
        number=number,
        state=state,
    )

    session.add(lp)
    session.commit()
    saved = LicensePlate.query.filter_by(number=number, state=state).first()
    assert saved is not None


def test_links_must_have_valid_urls(mockdata, faker):
    bad_url = faker.safe_domain_name()
    with raises(ValueError):
        Link(link_type="video", url=bad_url)


def test_links_can_be_saved_with_valid_urls(faker, mockdata, session):
    good_url = faker.url()
    li = Link(link_type="video", url=good_url)
    session.add(li)
    session.commit()
    saved = Link.query.filter_by(url=good_url).first()
    assert saved is not None


def test_incident_m2m_officers(mockdata, session):
    incident = Incident.query.first()
    officer = Officer(
        first_name="Test",
        last_name="McTesterson",
        middle_initial="T",
        race="WHITE",
        gender="M",
        birth_year=1990,
    )
    incident.officers.append(officer)
    session.add(incident)
    session.add(officer)
    session.commit()
    assert officer in incident.officers
    assert incident in officer.incidents


def test_incident_m2m_links(faker, mockdata, session):
    incident = Incident.query.first()
    link = Link(link_type="video", url=faker.url())
    incident.links.append(link)
    session.add(incident)
    session.add(link)
    session.commit()
    assert link in incident.links
    assert incident in link.incidents


def test_incident_m2m_license_plates(mockdata, session):
    incident = Incident.query.first()
    license_plate = LicensePlate(
        number="W23F43",
        state="DC",
    )
    incident.license_plates.append(license_plate)
    session.add(incident)
    session.add(license_plate)
    session.commit()
    assert license_plate in incident.license_plates
    assert incident in license_plate.incidents


def test_images_added_with_user_id(faker, mockdata, session):
    user_id = 1
    new_image = Image(
        filepath=faker.url(),
        hash_img="1234",
        is_tagged=False,
        department_id=1,
        taken_at=datetime.datetime.now(),
        created_by=user_id,
    )
    session.add(new_image)
    session.commit()
    saved = Image.query.filter_by(created_by=user_id).first()
    assert saved is not None


def test_salary_rounding_and_sorting(mockdata, session):
    officer = Officer.query.first()
    large_number = 123123456789.01
    small_number = 0.01
    session.add(
        Salary(
            officer_id=officer.id,
            salary=large_number,
            overtime_pay=large_number,
            year=2000,
            is_fiscal_year=False,
        )
    )

    session.add(
        Salary(
            officer_id=officer.id,
            salary=small_number,
            overtime_pay=small_number,
            year=2001,
            is_fiscal_year=False,
        )
    )

    session.commit()

    salaries = (
        Salary.query.filter_by(officer_id=officer.id)
        .order_by(Salary.salary.desc())
        .all()
    )

    assert salaries[0].salary == large_number
    assert salaries[0].overtime_pay == large_number
    assert salaries[-1].salary == small_number
    assert salaries[-1].overtime_pay == small_number


def test_officer_incident_sort_order(mockdata, session):
    officer = session.get(Officer, 1)

    sorted_incidents = sorted(
        officer.incidents,
        key=lambda i: (i.date, i.time),
        reverse=True,
    )

    assert officer.incidents == sorted_incidents


def test_user_approved(mockdata, session, faker):
    user = User(
        email=faker.company_email(),
        username=faker.word(),
        password=faker.word(),
    )
    session.add(user)
    session.commit()

    # Unapproved -> Approved
    user.approve_user(1, True)
    assert user.approved_at is not None
    assert user.approved_by == 1

    # Approved -> Approved
    old_approved_at = user.approved_at
    user.approve_user(1, True)
    assert user.approved_at == old_approved_at
    assert user.approved_by == 1

    # Approved -> Unapproved
    user.approve_user(1, False)
    assert user.approved_at is None
    assert user.approved_by is None

    # Unapproved -> Unapproved
    user.approve_user(1, False)
    assert user.approved_at is None
    assert user.approved_by is None


def test_user_confirmed(mockdata, session, faker):
    user = User(
        email=faker.company_email(),
        username=faker.word(),
        password=faker.word(),
    )
    session.add(user)
    session.commit()

    # Unconfirmed -> Confirmed
    user.confirm_user(1, True)
    assert user.confirmed_at is not None
    assert user.confirmed_by == 1

    # Confirmed -> Confirmed
    old_confirmed_at = user.confirmed_at
    user.confirm_user(1, True)
    assert user.confirmed_at == old_confirmed_at
    assert user.confirmed_by == 1

    # Confirmed -> Unconfirmed
    user.confirm_user(1, False)
    assert user.confirmed_at is None
    assert user.confirmed_by is None

    # Unconfirmed -> Unconfirmed
    user.confirm_user(1, False)
    assert user.confirmed_at is None
    assert user.confirmed_by is None


def test_user_disabled(mockdata, session, faker):
    user = User(
        email=faker.company_email(),
        username=faker.word(),
        password=faker.word(),
    )
    session.add(user)
    session.commit()

    # Undisabled -> Disabled
    user.disable_user(1, True)
    assert user.disabled_at is not None
    assert user.disabled_by == 1

    # Disabled -> Disabled
    old_disabled_at = user.disabled_at
    user.disable_user(1, True)
    assert user.disabled_at == old_disabled_at
    assert user.disabled_by == 1

    # Disabled -> Undisabled
    user.disable_user(1, False)
    assert user.disabled_at is None
    assert user.disabled_by is None

    # Undisabled -> Undisabled
    user.disable_user(1, False)
    assert user.disabled_at is None
    assert user.disabled_by is None


@pytest.mark.parametrize(
    "by_attr, at_attr",
    [
        ("approved_by", "approved_at"),
        ("confirmed_by", "confirmed_at"),
        ("disabled_by", "disabled_at"),
    ],
)
def test_user_constraints(mockdata, session, faker, by_attr, at_attr):
    now = datetime.datetime.now(datetime.timezone.utc)
    user = User(
        email=faker.company_email(),
        username=faker.word(),
        password=faker.word(),
    )
    session.add(user)
    session.commit()

    setattr(user, at_attr, now)
    setattr(user, by_attr, 1)
    session.commit()

    # Both or neither "_at" and "_by" must be set
    setattr(user, at_attr, None)
    setattr(user, by_attr, 1)
    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    "dialect_name,original_value,intermediate_value",
    [
        ("sqlite", None, None),
        (
            "sqlite",
            datetime.datetime(1980, 1, 1, hour=0, tzinfo=ZoneInfo("America/Chicago")),
            datetime.datetime(1980, 1, 1, hour=6),
        ),
        ("postgresql", None, None),
        (
            "postgresql",
            datetime.datetime(1980, 1, 1, hour=0, tzinfo=ZoneInfo("America/Chicago")),
            datetime.datetime(1980, 1, 1, hour=0, tzinfo=ZoneInfo("America/Chicago")),
        ),
    ],
)
def test_tzdatetime_type_decorator(dialect_name, original_value, intermediate_value):
    tzdt = TZDateTime(timezone=True)
    dialect = MagicMock()
    dialect.name = dialect_name

    value = tzdt.process_bind_param(original_value, dialect)
    assert intermediate_value == value

    value = tzdt.process_result_value(value, dialect)
    assert original_value == value
