import os
from contextlib import contextmanager

import pytest
from flask import current_app
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.sql.expression import func

from OpenOversight.app.models.database import Department, Incident, Officer, Unit, db
from OpenOversight.app.utils.constants import FILE_TYPE_HTML, KEY_OFFICERS_PER_PAGE
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.constants import ADMIN_USER_EMAIL


DESCRIPTION_CUTOFF = 700


@contextmanager
def wait_for_page_load(browser, timeout=10):
    old_page = browser.find_element_by_tag_name(FILE_TYPE_HTML)
    yield
    WebDriverWait(browser, timeout).until(expected_conditions.staleness_of(old_page))


def login_admin(browser, server_port):
    browser.get(f"http://localhost:{server_port}/auth/login")
    with wait_for_page_load(browser):
        elem = browser.find_element_by_id("email")
        elem.clear()
        elem.send_keys(ADMIN_USER_EMAIL)
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


def wait_for_element_to_be_visible(browser, locator, text, timeout=10):
    try:
        element_visible = expected_conditions.visibility_of_element_located(
            (locator, text)
        )
        WebDriverWait(browser, timeout).until(element_visible)
    except TimeoutException:
        pytest.fail("Timed out while waiting for element to become visible")


def test_user_can_load_homepage_and_get_to_form(mockdata, browser, server_port):
    browser.get(f"http://localhost:{server_port}")

    # Complainant loads homepage
    assert "OpenOversight" in browser.title
    with wait_for_page_load(browser):
        browser.find_element_by_id("cpd").click()

    page_text = browser.find_element_by_tag_name("body").text
    assert "Find an Officer" in page_text


def test_user_can_use_form_to_get_to_browse(mockdata, browser, server_port):
    browser.get(f"http://localhost:{server_port}/find")

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


def test_user_can_get_to_complaint(mockdata, browser, server_port):
    browser.get(
        f"http://localhost:{server_port}/complaints?officer_star=6265&"
        "officer_first_name=IVANA&officer_last_name=SNOTBALL&officer_middle_initial="
        "&officer_image=static%2Fimages%2Ftest_cop2.png"
    )

    wait_for_element(browser, By.TAG_NAME, "h1")
    # Complainant arrives at page with the badge number, name, and link
    # to complaint form

    title_text = browser.find_element_by_tag_name("h1").text
    assert "File a Complaint" in title_text


def test_officer_browse_pagination(mockdata, browser, server_port):
    total = Officer.query.filter_by(department_id=AC_DEPT).count()

    # first page of results
    browser.get(f"http://localhost:{server_port}/departments/{AC_DEPT}?page=1")
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    expected = f"Showing 1-{current_app.config[KEY_OFFICERS_PER_PAGE]} of {total}"
    assert expected in page_text

    # last page of results
    last_page_index = (total // current_app.config[KEY_OFFICERS_PER_PAGE]) + 1
    browser.get(
        f"http://localhost:{server_port}/departments/{AC_DEPT}?page={last_page_index}"
    )
    wait_for_element(browser, By.TAG_NAME, "body")
    page_text = browser.find_element_by_tag_name("body").text
    start_of_page = (
        current_app.config[KEY_OFFICERS_PER_PAGE]
        * (total // current_app.config[KEY_OFFICERS_PER_PAGE])
        + 1
    )
    expected = f"Showing {start_of_page}-{total} of {total}"
    assert expected in page_text


def test_find_officer_can_see_uii_question_for_depts_with_uiis(
    mockdata, browser, server_port
):
    browser.get(f"http://localhost:{server_port}/find")

    dept_with_uii = Department.query.filter(
        Department.unique_internal_identifier_label.isnot(None)
    ).first()
    dept_id = str(dept_with_uii.id)

    dept_selector = Select(browser.find_element_by_id("dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element_by_id("activate-step-2").click()

    page_text = browser.find_element_by_tag_name("body").text
    assert "Do you know any part of the Officer's" in page_text


def test_find_officer_cannot_see_uii_question_for_depts_without_uiis(
    mockdata, browser, server_port
):
    browser.get(f"http://localhost:{server_port}/find")

    dept_without_uii = Department.query.filter_by(
        unique_internal_identifier_label=None
    ).first()
    dept_id = str(dept_without_uii.id)

    dept_selector = Select(browser.find_element_by_id("dept"))
    dept_selector.select_by_value(dept_id)
    browser.find_element_by_id("activate-step-2").click()

    uii_elements = browser.find_elements_by_id("#uii-question")
    assert len(uii_elements) == 0


def test_incident_detail_display_read_more_button_for_descriptions_over_cutoff(
    mockdata, browser, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    result = browser.find_element_by_id("description-overflow-row_" + incident_id)
    assert result.is_displayed()


def test_incident_detail_truncate_description_for_descriptions_over_cutoff(
    mockdata, browser, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    # Check that the text is truncated and contains more than just the ellipsis
    truncated_text = browser.find_element(
        "id", "incident-description_" + incident_id
    ).text
    assert "…" in truncated_text
    # Include buffer for jinja rendered spaces
    assert DESCRIPTION_CUTOFF + 20 > len(truncated_text) > 100


def test_incident_detail_do_not_display_read_more_button_for_descriptions_under_cutoff(
    mockdata, browser, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get(f"http://localhost:{server_port}/officers/1")

    # Select incident for officer that has description under cutoff chars
    result = browser.find_element_by_id("description-overflow-row_1")
    assert not result.is_displayed()


def test_click_to_read_more_displays_full_description(mockdata, browser, server_port):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    original_description = incident_long_description.description.strip()
    incident_id = str(incident_long_description.id)

    button = browser.find_element_by_id("description-overflow-button_" + incident_id)
    button.click()

    description_text = browser.find_element_by_id(
        "incident-description_" + incident_id
    ).text.strip()
    assert len(description_text) == len(original_description)
    assert description_text == original_description


def test_click_to_read_more_hides_the_read_more_button(mockdata, browser, server_port):
    # Navigate to profile page for officer with short and long incident descriptions
    browser.get(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    button = browser.find_element_by_id("description-overflow-button_" + incident_id)
    button.click()

    buttonRow = browser.find_element_by_id("description-overflow-row_" + incident_id)
    assert not buttonRow.is_displayed()


def test_officer_form_has_units_alpha_sorted(mockdata, browser, server_port):
    login_admin(browser, server_port)

    # get the units from the DB in the sort we expect
    db_units_sorted = list(
        map(
            lambda x: x.description,
            db.session.query(Unit).order_by(Unit.description.asc()).all(),
        )
    )
    # the Select tag in the interface has a 'None' value at the start
    db_units_sorted.insert(0, "None")

    # Check for the Unit sort on the 'add officer' form
    browser.get(f"http://localhost:{server_port}/officers/new")
    unit_select = Select(browser.find_element_by_id("unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted

    # Check for the Unit sort on the 'add assignment' form
    browser.get(f"http://localhost:{server_port}/officers/1")
    unit_select = Select(browser.find_element_by_id("unit"))
    select_units_sorted = list(map(lambda x: x.text, unit_select.options))
    assert db_units_sorted == select_units_sorted


def test_edit_officer_form_coerces_none_race_or_gender_to_not_sure(
    mockdata, browser, server_port
):
    # Set NULL race and gender for officer 1
    db.session.execute(
        Officer.__table__.update().where(Officer.id == 1).values(race=None, gender=None)
    )
    db.session.commit()

    login_admin(browser, server_port)

    # Navigate to edit officer page for officer having NULL race and gender
    browser.get(f"http://localhost:{server_port}/officers/1/edit")

    wait_for_element(browser, By.ID, "gender")
    select = Select(browser.find_element_by_id("gender"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == "Not Sure"

    wait_for_element(browser, By.ID, "race")
    select = Select(browser.find_element_by_id("race"))
    selected_option = select.first_selected_option
    selected_text = selected_option.text
    assert selected_text == "Not Sure"


@pytest.mark.skip("Enable once real file upload in tests is supported.")
def test_image_classification_and_tagging(mockdata, browser, server_port):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    img_path = os.path.join(test_dir, "images/200Cat.jpeg")

    login_admin(browser, server_port)

    # 1. Create new department (to avoid mockdata)
    browser.get(f"http://localhost:{server_port}/departments/new")
    wait_for_page_load(browser)
    browser.find_element(By.ID, "name").send_keys("Auburn Police Department")
    browser.find_element(By.ID, "short_name").send_keys("APD")
    browser.find_element(By.ID, "submit").click()
    wait_for_page_load(browser)

    # 2. Add a new officer
    browser.get(f"http://localhost:{server_port}/officers/new")
    wait_for_page_load(browser)

    dept_select = Select(browser.find_element("id", "department"))
    dept_select.select_by_visible_text("Auburn Police Department")
    dept_id = dept_select.first_selected_option.get_attribute("value")

    browser.find_element(By.ID, "first_name").send_keys("Officer")
    browser.find_element(By.ID, "last_name").send_keys("Friendly")
    browser.find_element(By.ID, "submit").click()

    wait_for_page_load(browser)
    # expected url: http://localhost:{server_port}/submit_officer_images/officer/<id>
    officer_id = browser.current_url.split("/")[-1]

    # 3. Submit an image
    browser.get(f"http://localhost:{server_port}/submit")
    wait_for_page_load(browser)

    Select(browser.find_element("id", "department")).select_by_value(dept_id)

    # Submit files in selenium: https://stackoverflow.com/a/61566075
    wait_for_element(browser, By.CLASS_NAME, "dz-hidden-input")
    upload = browser.find_element(By.CLASS_NAME, "dz-hidden-input")
    upload.send_keys(img_path)
    wait_for_element(browser, By.CLASS_NAME, "dz-success")

    # 4. Classify the uploaded image
    browser.get(f"http://localhost:{server_port}/sort/departments/{dept_id}")

    # Check that image loaded correctly: https://stackoverflow.com/a/36296478
    wait_for_element(browser, By.TAG_NAME, "img")
    image = browser.find_element(By.TAG_NAME, "img")
    assert image.get_attribute("complete") == "true"
    assert int(image.get_attribute("naturalHeight")) > 0

    browser.find_element(By.ID, "answer-yes").click()

    wait_for_page_load(browser)
    page_text = browser.find_element(By.TAG_NAME, "body").text
    assert "All images have been classified!" in page_text

    # 5. Identify the new officer in the uploaded image
    browser.get(f"http://localhost:{server_port}/cop_faces/departments/{dept_id}")
    wait_for_page_load(browser)
    browser.find_element(By.ID, "officer_id").send_keys(officer_id)
    browser.find_element(By.CSS_SELECTOR, "input[value='Add identified face']").click()

    wait_for_page_load(browser)
    page_text = browser.find_element(By.TAG_NAME, "body").text
    assert "Tag added to database" in page_text

    # 6. Log out as admin
    browser.get(f"http://localhost:{server_port}/auth/logout")
    wait_for_page_load(browser)

    # 7. Check that the tag appears on the officer page
    browser.get(f"http://localhost:{server_port}/officers/{officer_id}")
    wait_for_page_load(browser)
    browser.find_element(By.CSS_SELECTOR, "a > img.officer-face").click()

    wait_for_page_load(browser)
    image = browser.find_element(By.TAG_NAME, "img")
    frame = browser.find_element(By.ID, "face-tag-frame")

    # 8. Check that the tag frame is fully contained within the image
    wait_for_element_to_be_visible(browser, By.ID, "face-tag-frame")
    assert image.location["x"] <= frame.location["x"]
    assert image.location["y"] <= frame.location["y"]
    assert (
        image.location["x"] + image.size["width"]
        >= frame.location["x"] + frame.size["width"]
    )
    assert (
        image.location["y"] + image.size["height"]
        >= frame.location["y"] + frame.size["height"]
    )
    assert image.location["y"] <= frame.location["y"]
