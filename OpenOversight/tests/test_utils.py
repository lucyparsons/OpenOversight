from mock import patch, Mock

import OpenOversight


# Utils tests
def test_race_filter_select_all_black_officers(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'BLACK', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': ''}
    )
    for element in results:
        assert element.race == 'BLACK'


def test_gender_filter_select_all_male_officers(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'M', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': ''}
    )
    for element in results:
        assert element.gender == 'M'


def test_rank_filter_select_all_commanders(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'COMMANDER',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': ''}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'COMMANDER'


def test_rank_filter_select_all_police_officers(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'PO',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': ''}
    )
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'PO'


def test_filter_by_name(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': 'J', 'badge': ''}
    )
    for element in results:
        assert 'J' in element.last_name


def test_filter_by_badge_no(mockdata):
    results = OpenOversight.app.utils.grab_officers(
        {'race': 'Not Sure', 'gender': 'Not Sure', 'rank': 'Not Sure',
         'min_age': 16, 'max_age': 85, 'name': '', 'badge': '12'}
    )
    for element in results:
        assignment = element.assignments.first()
        assert '12' in str(assignment.star_no)


def test_compute_hash(mockdata):
    hash_result = OpenOversight.app.utils.compute_hash('bacon')
    expected_hash = '9cca0703342e24806a9f64e08c053dca7f2cd90f10529af8ea872afb0a0c77d4'
    assert hash_result == expected_hash


def test_s3_url(mockdata):
    local_path = 'OpenOversight/app/static/images/test_cop1.png'

    mocked_connection = Mock()
    with patch('boto3.client', Mock(return_value=mocked_connection)):
        url = OpenOversight.app.utils.upload_file(local_path,
                                                  'doesntmatter.png',
                                                  'test_cop1.png')
    assert 'https' in url
    # url should show folder structure with first two chars as folder name
    assert 'te/st' in url


def test_user_cannot_submit_malicious_file(mockdata):
    file_to_submit = 'passwd'
    assert OpenOversight.app.utils.allowed_file(file_to_submit) is False


def test_user_cannot_submit_invalid_file_extension(mockdata):
    file_to_submit = 'tests/test_models.py'
    assert OpenOversight.app.utils.allowed_file(file_to_submit) is False
