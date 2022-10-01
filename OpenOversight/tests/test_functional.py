from __future__ import division

from contextlib import contextmanager

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.sql.expression import func

from OpenOversight.app.config import BaseConfig
from OpenOversight.app.models import Department, Incident, Officer, Unit, db


DESCRIPTION_CUTOFF = 700


@contextmanager
def wait_for_page_load(browser, timeout=10):
    old_page = browser.find_element("tag name", "html")
    yield
    WebDriverWait(browser, timeout).until(expected_conditions.staleness_of(old_page))


def login_admin(browser):
    browser.get("http://localhost:5000/auth/login")
    with wait_for_page_load(browser):
        elem = browser.find_element("id", "email")
        elem.clear()
        elem.send_keys("test@example.org")
        elem = browser.find_element("id", "password")
        elem.clear()
        elem.send_keys("testtest")
        with wait_for_page_load(browser):
            browser.find_element("id", "submit").click()
            wait_for_element(browser, By.TAG_NAME, "body")


def wait_for_element(browser, locator, text, timeout=10):
    try:
        element_present = expected_conditions.presence_of_element_located(
            (locator, text)
        )
        WebDriverWait(browser, timeout).until(element_present)
    except TimeoutException:
        pytest.fail("Timed out while waiting for element to appear")


@pytest.mark.acceptance
def test_user_can_load_homepage_and_get_to_form(mockdata, browser):
    browser.get("http://localhost:5000")

    # Complainant loads homepage
    assert "OpenOversight" in browser.title
    with wait_for_page_load(browser):
        browser.find_element("id", "cpd").click()

    page_text = browser.find_element("tag name", "body").text
    assert "Find an Officer" in page_text


@pytest.mark.acceptance
def test_user_can_use_form_to_get_to_browse(mockdata, browser):
    browser.get("http://localhost:5000/find")

    # Complainant selects department and proceeds to next step
    browser.find_element("id", "activate-step-2").click()

    # Complainant puts in what they remember about name/badge number and
    # proceeds to next step
    browser.find_element("id", "activate-step-3").click()

    # Complainant selects the officer rank and proceeds to next step
    browser.find_element("id", "activate-step-4").click()

    # Complainant fills out demographic information on officer
    # Complainant clicks generate list and gets list of officers
    with wait_for_page_load(browser):
        browser.find_element("name", "submit-officer-search-form").click()

    page_text = browser.find_element("tag name", "body").text
    assert "Filter officers" in page_text
    assert browser.find_element("id", "officer-profile-1")


@pytest.mark.acceptance
def test_user_can_get_to_complaint(mockdata, browser):
    browser.get(
        "http://localhost:5000/complaint?officer_star=6265&officer_first_name=IVANA&officer_last_name=SNOTBALL&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png"
    )

    wait_for_element(browser, By.TAG_NAME, "h1")
    # Complainant arrives at page with the badge number, name, and link
    # to complaint form

    title_text = browser.find_element("tag name", "h1").text
    assert "File a Complaint" in title_text


@pytest.mark.acceptance
def test_officer_browse_pagination(mockdata, browser):
    dept_id = 1
    total = Officer.query.filter_by(department_id=dept_id).count()
    perpage = BaseConfig.OFFICERS_PER_PAGE

    # first page of results
    browser.get("http://localhost:5000/department/{}?page=1".format(dept_id))
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element("tag name", "body").text
    expected = "Showing 1-{} of {}".format(perpage, total)
    assert expected in page_text

    # last page of results
    last_page_index = (total // perpage) + 1
    browser.get(
        "http://localhost:5000/department/{}?page={}".format(dept_id, last_page_index)
    )
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element("tag name", "body").text
    expected = "Showing {}-{} of {}".format(
        perpage * (total // perpage) + 1, total, total
    )
    assert expected in page_text


@pytest.mark.acceptance
def test_find_officer_can_see_uii_question_for_depts_with_uiis(mockdata, browser):
    browser.get("http://localhost:5000/find")

    dept_with_uii = Department.query.filter(
        Department.unique_internal_identifier_label.isnot(None)
    ).first()
    dept_id = str(dept_with_uii.id)

    dept_selector = Select(browser.find_element("id", "dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element("id", "activate-step-2").click()

    page_text = browser.find_element("tag name", "body").text
    assert "Do you know any part of the Officer's" in page_text


@pytest.mark.acceptance
def test_find_officer_cannot_see_uii_question_for_depts_without_uiis(mockdata, browser):
    browser.get("http://localhost:5000/find")

    dept_without_uii = Department.query.filter_by(
        unique_internal_identifier_label=None
    ).one_or_none()
    dept_id = str(dept_without_uii.id)

    dept_selector = Select(browser.find_element("id", "dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element("id", "activate-step-2").click()

    results = browser.find_elements("id", "#uii-question")
    assert len(results) == 0


@pytest.mark.acceptance
def test_incident_detail_display_read_more_button_for_descriptions_over_cutoff(
    mockdata, browser
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_descrip.id)

    result = browser.find_element("id", "description-overflow-row_" + incident_id)
    assert result.is_displayed()


@pytest.mark.acceptance
def test_incident_detail_truncate_description_for_descriptions_over_cutoff(
    mockdata, browser
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_descrip.id)

    # Check that the text is truncated and contains more than just the ellipsis
    truncated_text = browser.find_element(
        "id", "incident-description_" + incident_id
    ).text
    assert "…" in truncated_text
    # Include buffer for jinja rendered spaces
    assert DESCRIPTION_CUTOFF + 20 > len(truncated_text) > 100


@pytest.mark.acceptance
def test_incident_detail_do_not_display_read_more_button_for_descriptions_under_cutoff(
    mockdata, browser
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    # Select incident for officer that has description under cuttoff chars
    result = browser.find_element("id", "description-overflow-row_1")
    assert not result.is_displayed()


@pytest.mark.acceptance
def test_click_to_read_more_displays_full_description(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    orig_descrip = incident_long_descrip.description.strip()
    incident_id = str(incident_long_descrip.id)

    button = browser.find_element("id", "description-overflow-button_" + incident_id)
    button.click()

    description_text = browser.find_element(
        "id", "incident-description_" + incident_id
    ).text.strip()
    assert len(description_text) == len(orig_descrip)
    assert description_text == orig_descrip


@pytest.mark.acceptance
def test_click_to_read_more_hides_the_read_more_button(mockdata, browser):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get("http://localhost:5000/officer/1")

    incident_long_descrip = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_descrip.id)

    button = browser.find_element("id", "description-overflow-button_" + incident_id)
    button.click()

    buttonRow = browser.find_element("id", "description-overflow-row_" + incident_id)
    assert not buttonRow.is_displayed()


@pytest.mark.acceptance
def test_officer_form_has_units_alpha_sorted(mockdata, browser):
    login_admin(browser)

    # get the units from the DB in the sort we expect
    db_units_sorted = list(
        map(
            lambda x: x.descrip,
            db.session.query(Unit).order_by(Unit.descrip.asc()).all(),
        )
    )
    # the Select tag in the interface has a 'None' value at the start
    db_units_sorted.insert(0, "None")

    # Check for the Unit sort on the 'add officer' form
    browser.get("http://localhost:5000/officer/new")
    unit_select = Select(browser.find_element("id", "unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted

    # Check for the Unit sort on the 'add assignment' form
    browser.get("http://localhost:5000/officer/1")
    unit_select = Select(browser.find_element("id", "unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted


@pytest.mark.acceptance
def test_edit_officer_form_coerces_none_race_or_gender_to_not_sure(mockdata, browser):
    # Set NULL race and gender for officer 1
    db.session.execute(
        Officer.__table__.update().where(Officer.id == 1).values(race=None, gender=None)
    )
    db.session.commit()

    login_admin(browser)

    # Nagivate to edit officer page for officer having NULL race and gender
    browser.get("http://localhost:5000/officer/1/edit")

    wait_for_element(browser, By.ID, "gender")
    select = Select(browser.find_element("id", "gender"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == "Not Sure"

    wait_for_element(browser, By.ID, "race")
    select = Select(browser.find_element("id", "race"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == "Not Sure"
