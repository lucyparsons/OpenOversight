from mock import patch, Mock, MagicMock
import os
import OpenOversight
from OpenOversight.app.models import Image, Officer, Assignment
from OpenOversight.app.commands import bulk_add_officers
from OpenOversight.app.utils import get_officer
import pytest
import pandas as pd
import uuid


# Utils tests
def test_department_filter(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assert element.department == department


def test_race_filter_select_all_black_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['BLACK'], 'gender': ['Not Sure'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assert element.race in ('BLACK', 'Not Sure')


def test_gender_filter_select_all_male_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['M'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assert element.gender in ('M', 'Not Sure')


def test_rank_filter_select_all_commanders(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['COMMANDER'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assignment = element.assignments.first()
        assert assignment.rank in ('COMMANDER', 'Not Sure')


def test_rank_filter_select_all_police_officers(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['PO'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assignment = element.assignments.first()
        assert assignment.rank in ('PO', 'Not Sure')


def test_filter_by_name(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': 'J', 'badge': '',
         'dept': department}
    )
    for element in results.all():
        assert 'J' in element.last_name


def test_filters_do_not_exclude_officers_without_assignments(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    officer = OpenOversight.app.models.Officer(first_name='Rachel', last_name='S', department=department, birth_year=1992)
    results = OpenOversight.app.utils.grab_officers(
        {'race': [], 'gender': [], 'rank': [],
         'min_age': 16, 'max_age': 85, 'name': 'S', 'badge': '',
         'dept': department}
    )
    assert officer in results.all()


def test_filter_by_badge_no(mockdata):
    department = OpenOversight.app.models.Department.query.first()
    results = OpenOversight.app.utils.grab_officers(
        {'race': ['Not Sure'], 'gender': ['Not Sure'], 'rank': ['Not Sure'],
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '12',
         'dept': department}
    )
    for element in results.all():
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


def test_csv_import_new(csvfile):
    # Delete all current officers and assignments
    Assignment.query.delete()
    Officer.query.delete()

    assert Officer.query.count() == 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created > 0
    assert Officer.query.count() == n_created
    assert n_updated == 0


def test_csv_import_update(csvfile):
    n_existing = Officer.query.count()

    assert n_existing > 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)

    assert n_created == 0
    assert n_updated > 0
    assert Officer.query.count() == n_existing


def test_csv_import_idempotence(csvfile):
    # Delete all current officers and assignments
    Assignment.query.delete()
    Officer.query.delete()

    assert Officer.query.count() == 0

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created > 0
    assert n_updated == 0
    assert Officer.query.count() == n_created

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated > 0
    assert Officer.query.count() == n_updated


def test_csv_missing_required_field(csvfile):
    df = pd.read_csv(csvfile)
    df.drop(columns='first_name').to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert 'Missing required field' in str(exc.value)


def test_csv_missing_badge_and_uid(csvfile):
    df = pd.read_csv(csvfile)
    df.drop(columns=['star_no', 'unique_internal_identifier']).to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert 'CSV file must include either badge numbers or unique identifiers for officers' in str(exc.value)


def test_csv_non_existant_dept_id(csvfile):
    df = pd.read_csv(csvfile)
    df['department_id'] = 666
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert 'Department ID 666 not found' in str(exc.value)


def test_csv_officer_missing_badge_and_uid(csvfile):
    df = pd.read_csv(csvfile)
    df.loc[0, 'star_no'] = None
    df.loc[0, 'unique_internal_identifier'] = None
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert 'missing badge number and unique identifier' in str(exc.value)


def test_csv_changed_static_field(csvfile):
    df = pd.read_csv(csvfile)
    df.loc[0, 'birth_year'] = 666
    df.to_csv(csvfile)

    with pytest.raises(Exception) as exc:
        bulk_add_officers([csvfile])
    assert 'has differing birth_year field' in str(exc.value)


def test_csv_new_assignment(csvfile):
    # Delete all current officers and assignments
    Assignment.query.delete()
    Officer.query.delete()

    assert Officer.query.count() == 0

    df = pd.read_csv(csvfile)
    df.loc[0, 'rank'] = 'COMMANDER'
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created > 0
    assert n_updated == 0
    assert Officer.query.count() == n_created

    officer = get_officer(1, df.loc[0, 'star_no'], df.loc[0, 'first_name'], df.loc[0, 'last_name'])
    assert officer
    officer_id = officer.id
    assert len(list(officer.assignments)) == 1

    # Update rank
    df.loc[0, 'rank'] = 'CAPTAIN'
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated > 0
    assert Officer.query.count() == n_updated

    officer = Officer.query.filter_by(id=officer_id).one()
    assert len(list(officer.assignments)) == 2
    for assignment in officer.assignments:
        assert assignment.rank == 'COMMANDER' or assignment.rank == 'CAPTAIN'


def test_csv_new_name(csvfile):
    df = pd.read_csv(csvfile)
    officer_uid = df.loc[0, 'unique_internal_identifier']
    assert officer_uid

    df.loc[0, 'first_name'] = 'FOO'
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 0
    assert n_updated > 0

    officer = Officer.query.filter_by(unique_internal_identifier=officer_uid).one()

    assert officer.first_name == 'FOO'


def test_csv_new_officer(csvfile):
    df = pd.read_csv(csvfile)

    n_rows = len(df.index)
    assert n_rows > 0

    n_officers = Officer.query.count()
    assert n_officers > 0

    new_uid = str(uuid.uuid4())
    new_officer = {  # Must match fields in csvfile
        'department_id': 1,
        'unique_internal_identifier': new_uid,
        'first_name': 'FOO',
        'last_name': 'BAR',
        'middle_initial': None,
        'suffix': None,
        'gender': 'F',
        'race': 'BLACK',
        'employment_date': None,
        'birth_year': None,
        'star_no': 666,
        'rank': 'CAPTAIN',
        'unit': None,
        'star_date': None,
        'resign_date': None
    }
    df = df.append([new_officer])
    df.to_csv(csvfile)

    n_created, n_updated = bulk_add_officers([csvfile], standalone_mode=False)
    assert n_created == 1
    assert n_updated == n_rows

    officer = Officer.query.filter_by(unique_internal_identifier=new_uid).one()

    assert officer.first_name == 'FOO'
    assert Officer.query.count() == n_officers + 1
