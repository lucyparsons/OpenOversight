from __future__ import division
from contextlib import contextmanager
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from sqlalchemy.sql.expression import func
from OpenOversight.app.models import db, Officer, Incident, Department, Unit
from OpenOversight.app.config import BaseConfig


@contextmanager
def wait_for_page_load(browser, timeout=10):
    old_page = browser.find_element_by_tag_name('html')
    yield
    WebDriverWait(browser, timeout).until(
        expected_conditions.staleness_of(old_page)
    )


def login_admin(browser):
    browser.get("http://localhost:5000/auth/login")
    with wait_for_page_load(browser):
        elem = browser.find_element_by_id("email")
        elem.clear()
        elem.send_keys("test@example.org")
        elem = browser.find_element_by_id("password")
        elem.clear()
        elem.send_keys("testtest")
        with wait_for_page_load(browser):
            browser.find_element_by_id("submit").click()
            wait_for_element(browser, By.TAG_NAME, "body")


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


def test_user_can_use_form_to_get_to_browse(mockdata, browser):
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
    assert "Filter officers" in page_text
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
    browser.get("http://localhost:5000/department/{}?page=1"
                .format(dept_id))
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    expected = 'Showing 1-{} of {}'.format(perpage, total)
    assert expected in page_text

    # last page of results
    last_page_index = (total // perpage) + 1
    browser.get("http://localhost:5000/department/{}?page={}"
                .format(dept_id, last_page_index))
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    expected = ('Showing {}-{} of {}'
                .format(perpage * (total // perpage) + 1, total, total))
    assert expected in page_text


def test_last_name_capitalization(mockdata, browser):
    login_admin(browser)
    wait_for_element(browser, By.ID, "cpd")

    test_pairs = [("mcDonald", "McDonald"), ("Mei-Ying", "Mei-Ying")]

    for test_pair in test_pairs:
        test_input = test_pair[0]
        test_output = test_pair[1]

        # enter a last name to test
        browser.get("http://localhost:5000/officer/new")
        wait_for_element(browser, By.ID, "last_name")
        elem = browser.find_element_by_id("last_name")
        elem.clear()
        elem.send_keys(test_input)
        with wait_for_page_load(browser):
            browser.find_element_by_id("submit").click()

        # get past the "Submit images" page
        wait_for_element(browser, By.ID, "submit-officer-images")
        images_button = browser.find_element_by_css_selector("#submit-officer-images")
        with wait_for_page_load(browser):
            images_button.click()

        # check result
        wait_for_element(browser, By.TAG_NAME, "h1")
        rendered_field = browser.find_element_by_tag_name("h1").text
        rendered_name = rendered_field.split(":")[1].strip()
        assert rendered_name == test_output


def test_last_name_capitalization_short_name(mockdata, browser):
    login_admin(browser)
    wait_for_element(browser, By.ID, "cpd")

    test_pairs = [("G", "G"), ("oh", "Oh")]

    for test_pair in test_pairs:
        test_input = test_pair[0]
        test_output = test_pair[1]

        # enter a last name to test
        browser.get("http://localhost:5000/officer/new")
        wait_for_element(browser, By.ID, "last_name")
        elem = browser.find_element_by_id("last_name")
        elem.clear()
        elem.send_keys(test_input)
        with wait_for_page_load(browser):
            browser.find_element_by_id("submit").click()

        # get past the "Submit images" page
        wait_for_element(browser, By.ID, "submit-officer-images")
        images_button = browser.find_element_by_css_selector("#submit-officer-images")
        with wait_for_page_load(browser):
            images_button.click()

        # check result
        wait_for_element(browser, By.TAG_NAME, "h1")
        rendered_field = browser.find_element_by_tag_name("h1").text
        rendered_name = rendered_field.split(":")[1].strip()
        assert rendered_name == test_output


def test_find_officer_can_see_uii_question_for_depts_with_uiis(mockdata, browser):
    browser.get("http://localhost:5000/find")

    dept_with_uii = Department.query.filter(Department.unique_internal_identifier_label.isnot(None)).first()
    dept_id = str(dept_with_uii.id)

    dept_selector = Select(browser.find_element_by_id("dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element_by_id("activate-step-2").click()

    page_text = browser.find_element_by_tag_name("body").text
    assert "Do you know any part of the Officer's" in page_text


def test_find_officer_cannot_see_uii_question_for_depts_without_uiis(mockdata, browser):
    browser.get("http://localhost:5000/find")

    dept_without_uii = Department.query.filter_by(unique_internal_identifier_label=None).one_or_none()
    dept_id = str(dept_without_uii.id)

    dept_selector = Select(browser.find_element_by_id("dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element_by_id("activate-step-2").click()

    results = browser.find_elements_by_id("#uii-question")
    assert len(results) == 0


def test_incident_detail_display_read_more_button_for_descriptions_over_300_chars(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(func.length(Incident.description) > 300).one_or_none()
    incident_id = str(incident_long_descrip.id)

    result = browser.find_element_by_id("description-overflow-row_" + incident_id)
    assert result.is_displayed()


def test_incident_detail_do_not_display_read_more_button_for_descriptions_under_300_chars(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    # Select incident for officer that has description under 300 chars
    result = browser.find_element_by_id("description-overflow-row_1")
    assert not result.is_displayed()


def test_click_to_read_more_displays_full_description(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(func.length(Incident.description) > 300).one_or_none()
    orig_descrip = incident_long_descrip.description
    incident_id = str(incident_long_descrip.id)

    button = browser.find_element_by_id("description-overflow-button_" + incident_id)
    button.click()

    description_text = browser.find_element_by_id("incident-description_" + incident_id).text
    assert len(description_text) == len(orig_descrip)
    assert description_text == orig_descrip


def test_click_to_read_more_hides_the_read_more_button(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(func.length(Incident.description) > 300).one_or_none()
    incident_id = str(incident_long_descrip.id)

    button = browser.find_element_by_id("description-overflow-button_" + incident_id)
    button.click()

    buttonRow = browser.find_element_by_id("description-overflow-row_" + incident_id)
    assert not buttonRow.is_displayed()


def test_officer_form_has_units_alpha_sorted(mockdata, browser):
    login_admin(browser)

    # get the units from the DB in the sort we expect
    db_units_sorted = list(map(lambda x: x.descrip, db.session.query(Unit).order_by(Unit.descrip.asc()).all()))
    # the Select tag in the interface has a 'None' value at the start
    db_units_sorted.insert(0, 'None')

    # Check for the Unit sort on the 'add officer' form
    browser.get("http://localhost:5000/officer/new")
    unit_select = Select(browser.find_element_by_id("unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted

    # Check for the Unit sort on the 'add assignment' form
    browser.get("http://localhost:5000/officer/1")
    unit_select = Select(browser.find_element_by_id("unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted


def test_edit_officer_form_coerces_none_race_or_gender_to_not_sure(mockdata, browser):
    # Set NULL race and gender for officer 1
    db.session.execute(
        Officer.__table__.update().where(Officer.id == 1).values(race=None, gender=None))
    db.session.commit()

    login_admin(browser)

    # Nagivate to edit officer page for officer having NULL race and gender
    browser.get("http://localhost:5000/officer/1/edit")

    wait_for_element(browser, By.ID, "gender")
    select = Select(browser.find_element_by_id("gender"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == 'Not Sure'

    wait_for_element(browser, By.ID, "race")
    select = Select(browser.find_element_by_id("race"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == 'Not Sure'
