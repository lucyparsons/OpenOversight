from __future__ import division
from contextlib import contextmanager
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from OpenOversight.app.models import Officer
from OpenOversight.app.config import BaseConfig


@contextmanager
def wait_for_page_load(browser, timeout=10):
    old_page = browser.find_element_by_tag_name('html')
    yield
    WebDriverWait(browser, timeout).until(
        expected_conditions.staleness_of(old_page)
    )


def wait_for_element(browser, locator, text, timeout=10):
    try:
        element_present = expected_conditions.presence_of_element_located(
            (locator, text)
        )
        WebDriverWait(browser, timeout).until(element_present)
    except TimeoutException:
        pytest.fail("Timed out while waiting for element to appear")


def test_user_can_load_homepage_and_get_to_form(mockdata, browser):
    browser.get("http://localhost:5000")

    # Complainant loads homepage
    assert "OpenOversight" in browser.title
    with wait_for_page_load(browser):
        browser.find_element_by_id("cpd").click()

    page_text = browser.find_element_by_tag_name("body").text
    assert "Find an Officer" in page_text


def test_user_can_use_form_to_get_to_gallery(mockdata, browser):
    browser.get("http://localhost:5000/find")

    # Complainant selects department and proceeds to next step
    browser.find_element_by_id("activate-step-2").click()

    # Complainant puts in what they remember about name/badge number and
    # proceeds to next step
    browser.find_element_by_id("activate-step-3").click()

    # Complainant selects the officer rank and proceeds to next step
    browser.find_element_by_id("activate-step-4").click()

    # Complainant fills out demographic information on officer
    # Complainant clicks generate list and gets list of officers
    with wait_for_page_load(browser):
        browser.find_element_by_name("submit-officer-search-form").click()

    page_text = browser.find_element_by_tag_name("body").text
    assert "Digital Gallery" in page_text
    assert browser.find_element_by_id("officer-profile-1")


def test_user_can_get_to_complaint(mockdata, browser):
    browser.get("http://localhost:5000/complaint?officer_star=6265&officer_first_name=IVANA&officer_last_name=SNOTBALL&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png")

    wait_for_element(browser, By.TAG_NAME, "h1")
    # Complainant arrives at page with the badge number, name, and link
    # to complaint form

    title_text = browser.find_element_by_tag_name("h1").text
    assert "File a Complaint" in title_text


def test_officer_browse_pagination(mockdata, browser):
    dept_id = 1
    total = Officer.query.filter_by(department_id=dept_id).count()
    perpage = BaseConfig.OFFICERS_PER_PAGE

    # first page of results
    browser.get("http://localhost:5000/department/{}?from_search=False&page=1"
                .format(dept_id))
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    expected = 'Showing 1-{} of {}'.format(perpage, total)
    assert expected in page_text

    # last page of results
    last_page_index = (total // perpage) + 1
    browser.get("http://localhost:5000/department/{}?from_search=False&page={}"
                .format(dept_id, last_page_index))
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    expected = ('Showing {}-{} of {}'
                .format(perpage * (total // perpage) + 1, total, total))
    assert expected in page_text


def test_lastname_capitalization(mockdata, browser):
    browser.get("http://localhost:5000/auth/login")
    wait_for_page_load(browser)

    # get past the login page
    elem = browser.find_element_by_id("email")
    elem.clear()
    elem.send_keys("redshiftzero@example.org")
    elem = browser.find_element_by_id("password")
    elem.clear()
    elem.send_keys("cat")
    browser.find_element_by_id("submit").click()
    wait_for_element(browser, By.ID, "cpd")

    test_pairs = [("mcDonald", "McDonald"), ("Mei-Ying", "Mei-Ying"),
                  ("G", "G"), ("oh", "Oh")]

    for test_pair in test_pairs:
        test_input = test_pair[0]
        test_output = test_pair[1]

        # enter a last name to test
        browser.get("http://localhost:5000/officer/new")
        wait_for_element(browser, By.ID, "last_name")
        elem = browser.find_element_by_id("last_name")
        elem.clear()
        elem.send_keys(test_input)
        browser.find_element_by_id("submit").click()

        # check result
        wait_for_element(browser, By.TAG_NAME, "tbody")
        rendered_field = browser.find_element_by_tag_name("h1").text
        rendered_name = rendered_field.split(":")[1].strip()
        assert rendered_name == test_output
