import unittest

from app import app, utils
from app.models import Officer, Assignment, Image, Face


class TestUtils(unittest.TestCase):
    def test_race_filter_select_all_black_officers(self):
        results = utils.grab_officers({'race': 'BLACK', 'gender': 'Not Sure',
                                      'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                      'name': '', 'badge': ''})
        for element in results:
            self.assertEquals(element.race, 'BLACK')

    def test_gender_filter_select_all_male_officers(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'M',
                                      'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                      'name': '', 'badge': ''})
        for element in results:
            self.assertEquals(element.gender, 'M')

    def test_rank_filter_select_all_commanders(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'COMMANDER', 'min_age': 16, 'max_age': 85,
                                       'name': '', 'badge': ''})
        for element in results:
            assignment = element.assignments.first()
            self.assertEquals(assignment.rank, 'COMMANDER')

    def test_get_badge_number(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'COMMANDER', 'min_age': 16, 'max_age': 85,
                                       'name': '', 'badge': ''})
        for element in results:
            assignment = element.assignments.first()
            self.assertEquals(assignment.star_no, 1234)

    def test_filter_by_name(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                       'name': 'J', 'badge': ''})
        for element in results:
            self.assertIn('J', element.last_name)

    def test_filter_by_badge_no(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'Not Sure', 'min_age': 16, 'max_age': 85,
                                       'name': '', 'badge': '12'})
        for element in results:
            assignment = element.assignments.first()
            self.assertIn('12', str(assignment.star_no))
