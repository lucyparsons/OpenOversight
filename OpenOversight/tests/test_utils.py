from app import utils


# Utils tests
def test_race_filter_select_all_black_officers(mockdata):
    results = utils.grab_officers({'race': 'BLACK', 'gender': 'Not Sure',
                                   'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                   'name': '', 'badge': ''})
    for element in results:
        assert element.race == 'BLACK'


def test_gender_filter_select_all_male_officers(mockdata):
    results = utils.grab_officers({'race': 'Not Sure', 'gender': 'M',
                                   'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                   'name': '', 'badge': ''})
    for element in results:
        assert element.gender == 'M'


def test_rank_filter_select_all_commanders(mockdata):
    results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                   'rank': 'COMMANDER', 'min_age': 16, 'max_age': 85,
                                   'name': '', 'badge': ''})
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'COMMANDER'


def test_rank_filter_select_all_police_officers(mockdata):
    results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                   'rank': 'PO', 'min_age': 16, 'max_age': 85,
                                   'name': '', 'badge': ''})
    for element in results:
        assignment = element.assignments.first()
        assert assignment.rank == 'PO'


def test_filter_by_name(mockdata):
    results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                   'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                   'name': 'J', 'badge': ''})
    for element in results:
        assert 'J' in element.last_name


def test_filter_by_badge_no(mockdata):
    results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                   'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                   'name': '', 'badge': '12'})
    for element in results:
        assignment = element.assignments.first()
        assert '12' in str(assignment.star_no)


def test_allowed_filenames(app):
    extension = ['png', 'jpg', 'jpeg', 'mpeg', 'mp4']
    for e in extension:
        test_filename = 'test.{}'.format(e)
        assert utils.allowed_file(test_filename) == True


def test_not_allowed_filenames(app):
    test_filename = 'test.gif'
    assert utils.allowed_file(test_filename) == False
