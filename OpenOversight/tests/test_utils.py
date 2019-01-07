from mock import patch, Mock, MagicMock
import os
import OpenOversight
from OpenOversight.app.models import Image
from OpenOversight.app.commands import bulk_add_officers
import pytest
import pandas as pd


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
        assert element.race in ('BLACK', 'Not Sure')


def test_gender_filter_select_all_male_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'M', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert element.gender in ('M', 'Not Sure')


def test_rank_filter_select_all_commanders(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'COMMANDER',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank in ('COMMANDER', 'Not Sure')


def test_rank_filter_select_all_police_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'PO',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank in ('PO', 'Not Sure')


def test_filter_by_name(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': 'J', 'badge': '',
         'dept': department}
    )
    for element in results:
        assert 'J' in element.last_name


def test_filters_do_not_exclude_officers_without_assignments(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    officer = OpenOversight.app.models.Officer(first_name='Rachel', last_name='S', department=department, birth_year=1992)
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': 'S', 'badge': '',
         'dept': department}
    )
    assert officer in results


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
    hash_result = OpenOversight.app.utils.compute_hash(b'bacon')
    expected_hash = '9cca0703342e24806a9f64e08c053dca7f2cd90f10529af8ea872afb0a0c77d4'
    assert hash_result == expected_hash


def test_s3_upload_png(mockdata):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, '../app/static/images/test_cop1.png')

    mocked_connection = Mock()
    mocked_resource = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        with patch('boto3.resource', Mock(return_value=mocked_resource)):
            OpenOversight.app.utils.upload_file(local_path,
                                                'doesntmatter.png',
                                                'test_cop1.png')

    assert mocked_connection.method_calls[0][2]['ExtraArgs']['ContentType'] == 'image/png'


def test_s3_upload_jpeg(mockdata):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    local_path = os.path.join(test_dir, '../app/static/images/test_cop5.jpg')

    mocked_connection = Mock()
    mocked_resource = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        with patch('boto3.resource', Mock(return_value=mocked_resource)):
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


# Mock calls to upload_file
@patch('OpenOversight.app.utils.upload_file', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_get_uploaded_cropped_image_new_tag(mockdata):
    original_image = Image.query.first()

    # gives the correct local path so that Pimage can open the image
    original_image.filepath = 'file:///' + os.getcwd() + '/app/' + original_image.filepath
    original_image_count = Image.query.count()
    cropped_image = OpenOversight.app.utils.get_uploaded_cropped_image(original_image, (20, 50, 200, 200))

    assert type(cropped_image) == Image
    assert Image.query.count() == original_image_count + 1


@patch('OpenOversight.app.utils.upload_file', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_get_uploaded_cropped_image_existing_tag(mockdata):
    original_image = Image.query.first()
    # gives the correct local path so that Pimage can open the image
    original_image.filepath = 'file:///' + os.getcwd() + '/app/' + original_image.filepath

    first_crop = OpenOversight.app.utils.get_uploaded_cropped_image(original_image, (20, 50, 200, 200))
    second_crop = OpenOversight.app.utils.get_uploaded_cropped_image(original_image, (20, 50, 200, 200))

    assert first_crop.id == second_crop.id


@patch('OpenOversight.app.utils.upload_file', MagicMock(side_effect=ValueError('foo')))
def test_get_uploaded_cropped_image_s3_error(mockdata):
    original_image = Image.query.first()
    original_image.filepath = 'file:///' + os.getcwd() + '/app/' + original_image.filepath

    cropped_image = OpenOversight.app.utils.get_uploaded_cropped_image(original_image, (20, 50, 200, 200))

    assert cropped_image is None


def test_csv_missing_required_field(csvfile):
    df = pd.read_csv(csvfile)
    df.drop(columns='first_name').to_csv(csvfile)
    with pytest.raises(Exception, match='Missing required field'):
        bulk_add_officers([csvfile])
