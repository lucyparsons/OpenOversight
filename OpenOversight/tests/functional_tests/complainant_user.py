from selenium import webdriver
import unittest
import time


class PotentialComplainantTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(5)

    def tearDown(self):
        self.browser.quit()

    def test_user_can_use_form_to_get_to_complaint(self):
        self.browser.get("http://localhost:3000")

        # Complainant loads homepage
        self.assertIn("OpenOversight", self.browser.title)

        # Complainant clicks 'Try it' and gets to Form
        self.browser.find_element_by_link_text("Try it").click()
        self.assertIn("Find an Officer", self.browser.page_source)

        # Complainant submits default search params and gets list of officers
        self.browser.find_element_by_xpath("//input[@id='user-notification']").click()
        time.sleep(10)
        self.assertIn("Digital Gallery", self.browser.page_source)

        # Complainant clicks on first officer in results
        self.browser.find_element_by_link_text("That's the officer!").click()
        time.sleep(10)

        # Complainant arrives at page with the badge number, name, and link
        # to complaint form
        self.assertIn("File a Complaint", self.browser.page_source)

if __name__ == "__main__":
    unittest.main()
