from selenium import webdriver
import unittest

class PotentialComplainantTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_user_can_use_form_to_get_to_complaint(self):
        self.browser.get('http://localhost:3000')
        self.browser.implicitly_wait(3)

        # Complainant loads homepage
        self.assertIn('OpenOversight', self.browser.title)
        self.fail('Finish the test!')

        # Complainant clicks on 'Try This'


        # Complainant submits default search params


        # Complainant clicks on first officer in results


        # Complainant


if __name__ == '__main__':
    unittest.main()
