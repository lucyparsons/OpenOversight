import datetime
import time

from pytest import raises

from OpenOversight.app.models import (
    Assignment,
    Department,
    Face,
    Image,
    Incident,
    LicensePlate,
    Link,
    Location,
    Officer,
    Salary,
    Unit,
    User,
    db,
)


def test_department_repr(mockdata):
    department = Department.query.first()
    assert department.__repr__() == "<Department ID {}: {}>".format(
        department.id, department.name
    )


def test_officer_repr(mockdata):
    officer = Officer.query.first()
    if officer.unique_internal_identifier:
        assert officer.__repr__() == "<Officer ID {}: {} {} {} {} ({})>".format(
            officer.id,
            officer.first_name,
            officer.middle_initial,
            officer.last_name,
            officer.suffix,
            officer.unique_internal_identifier,
        )
    else:
        assert officer.__repr__() == "<Officer ID {}: {} {} {} {}>".format(
            officer.id,
            officer.first_name,
            officer.middle_initial,
            officer.last_name,
            officer.suffix,
        )


def test_assignment_repr(mockdata):
    assignment = Assignment.query.first()
    assert assignment.__repr__() == "<Assignment: ID {} : {}>".format(
        assignment.officer.id, assignment.star_no
    )


def test_image_repr(mockdata):
    image = Image.query.first()
    assert image.__repr__() == "<Image ID {}: {}>".format(image.id, image.filepath)


def test_face_repr(mockdata):
    face = Face.query.first()
    assert face.__repr__() == "<Tag ID {}: {} - {}>".format(
        face.id, face.officer_id, face.img_id
    )


def test_unit_repr(mockdata):
    unit = Unit.query.first()
    assert unit.__repr__() == "Unit: {}".format(unit.descrip)


def test_user_repr(mockdata):
    user = User(username="bacon")
    assert user.__repr__() == "<User '{}'>".format(user.username)


def test_salary_repr(mockdata):
    salary = Salary.query.first()
    assert salary.__repr__() == "<Salary: ID {} : {}".format(
        salary.officer_id, salary.salary
    )


def test_password_not_printed(mockdata):
    user = User(password="bacon")
    with raises(AttributeError):
        user.password


def test_password_set_success(mockdata):
    user = User(password="bacon")
    assert user.password_hash is not None


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


def test_valid_confirmation_token(mockdata):
    user = User(password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token()
    assert user.confirm(token) is True


def test_invalid_confirmation_token(mockdata):
    user1 = User(password="bacon")
    user2 = User(password="bacon")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_confirmation_token()
    assert user2.confirm(token) is False


def test_expired_confirmation_token(mockdata):
    user = User(password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token(1)
    time.sleep(2)
    assert user.confirm(token) is False


def test_valid_reset_token(mockdata):
    user = User(password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_reset_token()
    assert user.reset_password(token, "vegan bacon") is True
    assert user.verify_password("vegan bacon") is True


def test_invalid_reset_token(mockdata):
    user1 = User(password="bacon")
    user2 = User(password="vegan bacon")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_reset_token()
    assert user2.reset_password(token, "tempeh") is False
    assert user2.verify_password("vegan bacon") is True


def test_expired_reset_token(mockdata):
    user = User(password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_reset_token(expiration=-1)
    assert user.reset_password(token, "tempeh") is False
    assert user.verify_password("bacon") is True


def test_valid_email_change_token(mockdata):
    user = User(email="brian@example.com", password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_email_change_token("lucy@example.org")
    assert user.change_email(token) is True
    assert user.email == "lucy@example.org"


def test_email_change_token_no_email(mockdata):
    user = User(email="brian@example.com", password="bacon")
    db.session.add(user)
    db.session.commit()
    token = user.generate_email_change_token(None)
    assert user.change_email(token) is False
    assert user.email == "brian@example.com"


def test_invalid_email_change_token(mockdata):
    user1 = User(email="jen@example.com", password="cat")
    user2 = User(email="freddy@example.com", password="dog")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user1.generate_email_change_token("mason@example.net")
    assert user2.change_email(token) is False
    assert user2.email == "freddy@example.com"


def test_expired_email_change_token(mockdata):
    user = User(email="jen@example.com", password="cat")
    db.session.add(user)
    db.session.commit()
    token = user.generate_email_change_token("mason@example.net", expiration=-1)
    assert user.change_email(token) is False
    assert user.email == "jen@example.com"


def test_duplicate_email_change_token(mockdata):
    user1 = User(email="alice@example.com", password="cat")
    user2 = User(email="bob@example.org", password="dog")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    token = user2.generate_email_change_token("alice@example.com")
    assert user2.change_email(token) is False
    assert user2.email == "bob@example.org"


def test_area_coordinator_with_dept_is_valid(mockdata):
    user1 = User(
        email="alice@example.com",
        username="me",
        password="cat",
        is_area_coordinator=True,
        ac_department_id=1,
    )
    db.session.add(user1)
    db.session.commit()
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


def test_locations_can_be_saved_with_valid_zip_codes(mockdata):
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
    db.session.add(lo)
    db.session.commit()
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


def test_locations_can_be_saved_with_valid_states(mockdata):
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

    db.session.add(lo)
    db.session.commit()
    saved = Location.query.filter_by(city=city, state=state).first()
    assert saved is not None


def test_license_plates_must_have_valid_states(mockdata):
    with raises(ValueError):
        LicensePlate(number="603EEE", state="JK")


def test_license_plates_can_be_saved_with_valid_states(mockdata):
    state = "AZ"
    number = "603RRR"
    lp = LicensePlate(
        number=number,
        state=state,
    )

    db.session.add(lp)
    db.session.commit()
    saved = LicensePlate.query.filter_by(number=number, state=state).first()
    assert saved is not None


def test_links_must_have_valid_urls(mockdata):
    bad_url = "www.rachel.com"
    with raises(ValueError):
        Link(link_type="video", url=bad_url)


def test_links_can_be_saved_with_valid_urls(mockdata):
    good_url = "http://www.rachel.com"
    li = Link(link_type="video", url=good_url)
    db.session.add(li)
    db.session.commit()
    saved = Link.query.filter_by(url=good_url).first()
    assert saved is not None


def test_incident_m2m_officers(mockdata):
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
    db.session.add(incident)
    db.session.add(officer)
    db.session.commit()
    assert officer in incident.officers
    assert incident in officer.incidents


def test_incident_m2m_links(mockdata):
    incident = Incident.query.first()
    link = Link(link_type="video", url="http://www.lulz.com")
    incident.links.append(link)
    db.session.add(incident)
    db.session.add(link)
    db.session.commit()
    assert link in incident.links
    assert incident in link.incidents


def test_incident_m2m_license_plates(mockdata):
    incident = Incident.query.first()
    license_plate = LicensePlate(
        number="W23F43",
        state="DC",
    )
    incident.license_plates.append(license_plate)
    db.session.add(incident)
    db.session.add(license_plate)
    db.session.commit()
    assert license_plate in incident.license_plates
    assert incident in license_plate.incidents


def test_images_added_with_user_id(mockdata):
    user_id = 1
    new_image = Image(
        filepath="http://www.example.com",
        hash_img="1234",
        is_tagged=False,
        date_image_inserted=datetime.datetime.now(),
        department_id=1,
        date_image_taken=datetime.datetime.now(),
        user_id=user_id,
    )
    db.session.add(new_image)
    db.session.commit()
    saved = Image.query.filter_by(user_id=user_id).first()
    assert saved is not None
