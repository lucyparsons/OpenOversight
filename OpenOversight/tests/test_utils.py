from datetime import datetime, timedelta
from mock import patch, Mock
import os
import OpenOversight


# Utils tests
def test_department_filter(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert element.department == department


def test_race_filter_select_all_black_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'BLACK', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert element.race == 'BLACK'


def test_gender_filter_select_all_male_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'M', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert element.gender == 'M'


def test_rank_filter_select_all_commanders(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'COMMANDER',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'COMMANDER'


def test_rank_filter_select_all_police_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'PO',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'PO'


def test_filter_by_name(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': 'J', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert 'J' in element.last_name


def test_filter_by_badge_no(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '12',
         'dept': department}
    )
    for element in results:
        assignment = element.assignments.first()
        assert '12' in str(assignment.star_no)


def test_compute_hash(mockdata):
    hash_result = OpenOversight.app.utils.compute_hash('bacon')
    expected_hash = '9cca0703342e24806a9f64e08c053dca7f2cd90f10529af8ea872afb0a0c77d4'
    assert hash_result == expected_hash


def test_s3_upload_png(mockdata):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, '../app/static/images/test_cop1.png')

    mocked_connection = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        url = OpenOversight.app.utils.upload_file(local_path,
                                                  'doesntmatter.png',
                                                  'test_cop1.png')
    assert 'https' in url
    # url should show folder structure with first two chars as folder name
    assert 'te/st' in url
    assert mocked_connection.method_calls[0][2]['ExtraArgs']['ContentType'] == 'image/png'


def test_s3_upload_jpeg(mockdata):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, '../app/static/images/test_cop5.jpg')

    mocked_connection = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        OpenOversight.app.utils.upload_file(local_path,
                                            'doesntmatter.jpg',
                                            'test_cop5.jpg')
    assert mocked_connection.method_calls[0][2]['ExtraArgs']['ContentType'] == 'image/jpeg'


def test_user_can_submit_allowed_file(mockdata):
    for file_to_submit in ['valid_photo.png', 'valid_photo.jpg', 'valid.photo.jpg', 'valid_photo.PNG', 'valid_photo.JPG']:
        assert OpenOversight.app.utils.allowed_file(file_to_submit) is True


def test_user_cannot_submit_malicious_file(mockdata):
    file_to_submit = 'passwd'
    assert OpenOversight.app.utils.allowed_file(file_to_submit) is False


def test_user_cannot_submit_invalid_file_extension(mockdata):
    file_to_submit = 'tests/test_models.py'
    assert OpenOversight.app.utils.allowed_file(file_to_submit) is False


def test_unit_choices(mockdata):
    unit_choices = [str(x) for x in OpenOversight.app.utils.unit_choices()]
    assert 'Unit: Bureau of Organized Crime' in unit_choices


def test_get_timeline_sorted_list(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    officer = OpenOversight.app.models.Officer(
        last_name='Timeline', first_name='Test',
        middle_initial='T',
        race='WHITE', gender='FEMALE',
        birth_year=1960,
        employment_date=datetime(1960 + 20, 4, 4, 1, 1, 1),
        department_id=department.id)
    OpenOversight.app.models.db.session.add(officer)
    OpenOversight.app.models.db.session.commit()

    time_now = datetime.now()
    image1 = OpenOversight.app.models.Image(
        filepath='beep',
        department_id=department.id,
        date_image_inserted=time_now - timedelta(days=1)
    )
    image2 = OpenOversight.app.models.Image(filepath='boop',
                                            department_id=department.id,
                                            date_image_inserted=time_now)
    OpenOversight.app.models.db.session.add_all([image1, image2])
    OpenOversight.app.models.db.session.commit()

    face1 = OpenOversight.app.models.Face(officer_id=officer.id,
                                          img_id=image1.id)
    face2 = OpenOversight.app.models.Face(officer_id=officer.id,
                                          img_id=image2.id)
    OpenOversight.app.models.db.session.add_all([face1, face2])
    OpenOversight.app.models.db.session.commit()

    faces = OpenOversight.app.models.Face \
                         .query.filter_by(officer_id=officer.id).all()

    events = OpenOversight.app.utils.get_timeline(faces)

    assert events[0]["date_image_inserted"] == time_now
    assert events[0]["image_id"] == image2.id

    # Older event should be second in the timeline
    assert events[1]["date_image_inserted"] == time_now - timedelta(days=1)
    assert events[1]["image_id"] == image1.id
