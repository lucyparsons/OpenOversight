from mock import patch, Mock, MagicMock
from flask import current_app
from flask_login import current_user
from io import BytesIO
import OpenOversight
from OpenOversight.app.models import Image
from OpenOversight.app.utils import upload_image_to_s3_and_store_in_db, crop_image
from OpenOversight.tests.routes.route_helpers import login_user
import pytest


# Utils tests

def test_department_filter(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department, 'unique_internal_identifier': ''}
    )
    for element in results.all():
        assert element.department == department


def test_race_filter_select_all_black_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['BLACK'], 'dept': department}
    )
    for element in results.all():
        assert element.race in ('BLACK', 'Not Sure')


def test_gender_filter_select_all_male_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'gender': ['M'], 'dept': department}
    )
    for element in results.all():
        assert element.gender in ('M', 'Not Sure')


def test_rank_filter_select_all_commanders(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'rank': ['Commander'], 'dept': department}
    )
    for element in results.all():
        assignment = element.assignments.first()
        assert assignment.job.job_title in ('Commander', 'Not Sure')


def test_rank_filter_select_all_police_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'rank': ['Police Officer'], 'dept': department}
    )
    for element in results.all():
        assignment = element.assignments.first()
        assert assignment.job.job_title in ('Police Officer', 'Not Sure')


def test_filter_by_name(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'name': 'J', 'dept': department}
    )
    for element in results.all():
        assert 'J' in element.last_name


def test_filters_do_not_exclude_officers_without_assignments(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    officer = OpenOversight.app.models.Officer(first_name='Rachel', last_name='S', department=department, birth_year=1992)
    results = OpenOversight.app.utils.grab_officers(
        {'name': 'S', 'dept': department}
    )
    assert officer in results.all()


def test_filter_by_badge_no(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'badge': '12', 'dept': department}
    )
    for element in results.all():
        assignment = element.assignments.first()
        assert '12' in str(assignment.star_no)


def test_filter_by_full_unique_internal_identifier_returns_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    target_unique_internal_id = OpenOversight.app.models.Officer.query.first().unique_internal_identifier
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department, 'unique_internal_identifier': target_unique_internal_id}
    )
    for element in results:
        returned_unique_internal_id = element.unique_internal_identifier
        assert returned_unique_internal_id == target_unique_internal_id


def test_filter_by_partial_unique_internal_identifier_returns_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    identifier = OpenOversight.app.models.Officer.query.first().unique_internal_identifier
    partial_identifier = identifier[:len(identifier) // 2]
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department, 'unique_internal_identifier': partial_identifier}
    )
    for element in results:
        returned_identifier = element.unique_internal_identifier
        assert returned_identifier == identifier


def test_compute_hash(mockdata):
    hash_result = OpenOversight.app.utils.compute_hash(b'bacon')
    expected_hash = '9cca0703342e24806a9f64e08c053dca7f2cd90f10529af8ea872afb0a0c77d4'
    assert hash_result == expected_hash


def test_s3_upload_png(mockdata, test_png_BytesIO):
    mocked_connection = Mock()
    mocked_resource = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        with patch('boto3.resource', Mock(return_value=mocked_resource)):
            OpenOversight.app.utils.upload_obj_to_s3(test_png_BytesIO, 'test_cop1.png')

    assert mocked_connection.method_calls[0][2]['ExtraArgs']['ContentType'] == 'image/png'


def test_s3_upload_jpeg(mockdata, test_jpg_BytesIO):
    mocked_connection = Mock()
    mocked_resource = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        with patch('boto3.resource', Mock(return_value=mocked_resource)):
            OpenOversight.app.utils.upload_obj_to_s3(test_jpg_BytesIO, 'test_cop5.jpg')

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


@patch('OpenOversight.app.utils.upload_obj_to_s3', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_upload_image_to_s3_and_store_in_db_increases_images_in_db(mockdata, test_png_BytesIO, client):
    original_image_count = Image.query.count()

    upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
    assert Image.query.count() == original_image_count + 1


@patch('OpenOversight.app.utils.upload_obj_to_s3', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_upload_existing_image_to_s3_and_store_in_db_returns_existing_image(mockdata, test_png_BytesIO, client):
    firstUpload = upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
    secondUpload = upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
    assert type(secondUpload) == Image
    assert firstUpload.id == secondUpload.id


@patch('OpenOversight.app.utils.upload_obj_to_s3', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_upload_image_to_s3_and_store_in_db_does_not_set_tagged(mockdata, test_png_BytesIO, client):
    upload = upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
    assert not upload.is_tagged


@patch('OpenOversight.app.utils.upload_obj_to_s3', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_upload_image_to_s3_and_store_in_db_saves_filename_in_correct_format(mockdata, test_png_BytesIO, client):
    mocked_connection = Mock()
    mocked_resource = Mock()

    with patch('boto3.client', Mock(return_value=mocked_connection)):
        with patch('boto3.resource', Mock(return_value=mocked_resource)):
            upload = upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
            filename = upload.filepath.split('/')[-1]
            filename_parts = filename.split('.')
            assert len(filename_parts) == 2


def test_upload_image_to_s3_and_store_in_db_throws_exception_for_unrecognized_format(mockdata, client):
    with pytest.raises(ValueError):
        upload_image_to_s3_and_store_in_db(BytesIO(b'invalid-image'), 1, 1)


@patch('OpenOversight.app.utils.upload_obj_to_s3', MagicMock(return_value='https://s3-some-bucket/someaddress.jpg'))
def test_upload_image_to_s3_and_store_in_db_does_not_throw_exception_for_recognized_format(mockdata, test_png_BytesIO, client):
    try:
        upload_image_to_s3_and_store_in_db(test_png_BytesIO, 1, 1)
    except ValueError:
        pytest.fail("Unexpected value error")


def test_crop_image_calls_upload_image_to_s3_and_store_in_db_with_user_id(mockdata, client):
    with current_app.test_request_context():
        login_user(client)
        department = OpenOversight.app.models.Department.query.first()
        image = OpenOversight.app.models.Image.query.first()

        with patch('OpenOversight.app.utils.upload_image_to_s3_and_store_in_db') as upload_image_to_s3_and_store_in_db:
            crop_image(image, None, department.id)

            assert current_user.get_id() in upload_image_to_s3_and_store_in_db.call_args[0]
