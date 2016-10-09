import unittest

from app import app, utils
from app.models import Officer, Assignment, Image, Face


class TestUtils(unittest.TestCase):
    def test_race_filter_select_all_black_officers(self):
        results = utils.grab_officers({'race': 'BLACK', 'gender': 'Not Sure',
                                      'rank': 'Not Sure', 'min_age': 16, 'max_age': 85})
        for element in results:
            self.assertEquals(element.Officer.race, 'BLACK')

    def test_gender_filter_select_all_male_officers(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'M',
                                      'rank': 'Not Sure', 'min_age': 16, 'max_age': 85})
        for element in results:
            self.assertEquals(element.Officer.gender, 'M')

    def test_rank_filter_select_all_commanders(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'COMMANDER', 'min_age': 16, 'max_age': 85})
        for element in results:
            self.assertEquals(element.Assignment.rank, 'COMMANDER')

    def test_get_badge_number(self):
        results = utils.grab_officers({'race': 'Not Sure', 'gender': 'Not Sure',
                                       'rank': 'COMMANDER', 'min_age': 16, 'max_age': 85})
        for element in results:
            self.assertEquals(element.Assignment.star_no, 1234)

    def test_no_face_found(self):
        result = utils.grab_officer_faces([0])
        self.assertEquals(result[0], 'https://placehold.it/200x200')

    def test_found_face(self):
        result = utils.grab_officer_faces([1])
        self.assertEquals(result[1], u'static/images/test_cop1.png')