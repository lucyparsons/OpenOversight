import os
import re
from unittest import skip

from flask import current_app
from playwright.sync_api import expect
from sqlalchemy.sql.expression import func

from OpenOversight.app.models.database import Department, Incident, Officer, Unit
from OpenOversight.app.utils.constants import KEY_OFFICERS_PER_PAGE
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.constants import ADMIN_USER_EMAIL


DESCRIPTION_CUTOFF = 700


def expect_banner_with_text(page, text):
    banner = page.get_by_text(text)
    expect(banner).to_be_visible()
    # Close banner to make sure it doesn't obscure other elements
    banner.locator(".btn-close").click()


def login_admin(page, server_port):
    page.goto(f"http://localhost:{server_port}/auth/login")
    page.locator("#email").fill(ADMIN_USER_EMAIL)
    page.locator("#password").fill("testtest")
    page.locator("#submit").click()
    page.wait_for_load_state()


def logout(page, server_port):
    page.goto(f"http://localhost:{server_port}/auth/logout")
    expect_banner_with_text(page, "You have been logged out.")


def submit_image_to_dropzone(page, img_path):
    page.locator(".dz-hidden-input").set_input_files(img_path)
    expect(page.locator(".dz-success")).to_be_visible()


def test_user_can_load_homepage_and_get_to_form(mockdata, page, server_port):
    page.goto(f"http://localhost:{server_port}")

    # Complainant loads homepage
    expect(page).to_have_title(re.compile(r"OpenOversight.*"))
    page.locator("#cpd").click()

    expect(page).to_have_title(re.compile(r"Find an officer.*"))


def test_user_can_get_to_complaint(page, server_port):
    page.goto(
        f"http://localhost:{server_port}/complaints?officer_star=6265&"
        "officer_first_name=IVANA&officer_last_name=SNOTBALL&officer_middle_initial="
        "&officer_image=static%2Fimages%2Ftest_cop2.png"
    )

    # Complainant arrives at page with the badge number, name, and link
    # to complaint form
    expect(page.get_by_text("File a Complaint")).to_be_visible()


def test_officer_browse_pagination(mockdata, page, server_port):
    total = Officer.query.filter_by(department_id=AC_DEPT).count()

    # first page of results
    page.goto(
        f"http://localhost:{server_port}/departments/{AC_DEPT}?page=1&gender=Not+Sure"
    )
    expected = f"Showing 1-{current_app.config[KEY_OFFICERS_PER_PAGE]} of {total}"
    expect(page.get_by_text(expected).first).to_be_visible()

    # check that "Next" pagination link does not automatically add require_photo parameter
    next_link = page.locator('//li[@class="next"]/a').first.get_attribute("href")
    assert "gender" in next_link
    assert "require_photo" not in next_link

    # last page of results
    last_page_index = (total // current_app.config[KEY_OFFICERS_PER_PAGE]) + 1
    page.goto(
        f"http://localhost:{server_port}/departments/{AC_DEPT}?page={last_page_index}&gender=Not+Sure"
    )
    start_of_page = (
        current_app.config[KEY_OFFICERS_PER_PAGE]
        * (total // current_app.config[KEY_OFFICERS_PER_PAGE])
        + 1
    )
    expected = f"Showing {start_of_page}-{total} of {total}"
    expect(page.get_by_text(expected).first).to_be_visible()

    # check that "Previous" pagination link does not automatically add require_photo parameter
    previous_link = page.locator("li.previous a").first.get_attribute("href")
    assert "gender" in previous_link
    assert "require_photo" not in previous_link


def test_find_officer_can_see_uii_question_for_depts_with_uiis(
    mockdata, page, server_port
):
    page.goto(f"http://localhost:{server_port}/find")

    dept_with_uii = Department.query.filter(
        Department.unique_internal_identifier_label.is_not(None)
    ).first()

    page.locator("#dept").select_option(str(dept_with_uii.id))
    expect(page.locator("#uii-question")).to_be_visible()


def test_find_officer_cannot_see_uii_question_for_depts_without_uiis(
    mockdata, page, server_port
):
    page.goto(f"http://localhost:{server_port}/find")

    dept_without_uii = Department.query.filter_by(
        unique_internal_identifier_label=None
    ).first()

    page.locator("#dept").select_option(str(dept_without_uii.id))
    expect(page.locator("#uii-question")).to_be_hidden()


def test_incident_detail_display_read_more_button_for_descriptions_over_cutoff(
    mockdata, page, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    page.goto(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    expect(page.locator("#description-overflow-row_" + incident_id)).to_be_visible()


def test_incident_detail_truncate_description_for_descriptions_over_cutoff(
    mockdata, page, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    page.goto(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    # Check that the text is truncated and contains more than just the ellipsis
    truncated_text = page.locator("#incident-description_" + incident_id).inner_text()
    assert "…" in truncated_text
    # Include buffer for jinja rendered spaces
    assert DESCRIPTION_CUTOFF + 20 > len(truncated_text) > 100


def test_incident_detail_do_not_display_read_more_button_for_descriptions_under_cutoff(
    mockdata, page, server_port
):
    # Navigate to profile page for officer with short and long incident descriptions
    page.goto(f"http://localhost:{server_port}/officers/1")

    # Select incident for officer that has description under cutoff chars
    expect(page.locator("#description-overflow-row_1")).to_be_hidden()


def test_click_to_read_more_displays_full_description(mockdata, page, server_port):
    # Navigate to profile page for officer with short and long incident descriptions
    page.goto(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    original_description = incident_long_description.description.strip()
    incident_id = str(incident_long_description.id)

    page.locator("#description-overflow-button_" + incident_id).click()

    description_text = (
        page.locator("#incident-description_" + incident_id).inner_text().strip()
    )
    assert len(description_text) == len(original_description)
    assert description_text == original_description


def test_click_to_read_more_hides_the_read_more_button(mockdata, page, server_port):
    # Navigate to profile page for officer with short and long incident descriptions
    page.goto(f"http://localhost:{server_port}/officers/1")

    incident_long_description = Incident.query.filter(
        func.length(Incident.description) > DESCRIPTION_CUTOFF
    ).one_or_none()
    incident_id = str(incident_long_description.id)

    page.locator("#description-overflow-button_" + incident_id).click()

    expect(page.locator("#description-overflow-row_" + incident_id)).to_be_hidden()


def test_officer_form_has_units_alpha_sorted(page, server_port, session):
    login_admin(page, server_port)

    # get the units from the DB in the sort we expect
    db_units_sorted = [
        x.description
        for x in session.query(Unit).order_by(Unit.description.asc()).all()
    ]
    # the Select tag in the interface has a 'None' value at the start
    db_units_sorted.insert(0, "None")

    # Check for the Unit sort on the 'add officer' form
    page.goto(f"http://localhost:{server_port}/officers/new")
    select_units_sorted = page.locator("#unit").evaluate(
        "select => Array.from(select).map(option => option.label)"
    )
    assert db_units_sorted == select_units_sorted

    # Check for the Unit sort on the 'add assignment' form
    page.goto(f"http://localhost:{server_port}/officers/1")
    select_units_sorted = page.locator("#unit").evaluate(
        "select => Array.from(select).map(option => option.label)"
    )
    assert db_units_sorted == select_units_sorted


def test_edit_officer_form_coerces_none_race_or_gender_to_not_sure(
    page, server_port, session
):
    # Set NULL race and gender for officer 1
    session.execute(
        Officer.__table__.update().where(Officer.id == 1).values(race=None, gender=None)
    )
    session.commit()

    login_admin(page, server_port)

    # Navigate to edit officer page for officer having NULL race and gender
    page.goto(f"http://localhost:{server_port}/officers/1/edit")

    select = page.locator("#gender")
    selected_text = select.evaluate("select => select.selectedOptions[0].label")
    assert selected_text == "Not Sure"

    select = page.locator("#race")
    selected_text = select.evaluate("select => select.selectedOptions[0].label")
    assert selected_text == "Not Sure"


@skip("Continually fails, S3 mock seems wonky")
def test_image_classification_and_tagging(page, server_port, session):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    img_path = os.path.join(test_dir, "images/200Cat.jpeg")
    star_no = 1312

    login_admin(page, server_port)

    # 1. Create new department (to avoid mockdata)
    page.goto(f"http://localhost:{server_port}/departments/new")
    page.locator("#name").fill("Auburn Police Department")
    page.locator("#short_name").fill("APD")
    page.locator("#state").select_option("WA")
    page.locator("#submit").click()

    # 2. Add a new officer
    page.goto(f"http://localhost:{server_port}/officers/new")

    dept_select = page.locator("#department")
    dept_select.select_option(label="Auburn Police Department")
    dept_id = dept_select.evaluate("select => select.selectedOptions[0].value")

    page.locator("#first_name").fill("Officer")
    page.locator("#last_name").fill("Friendly")
    page.locator("#star_no").fill(str(star_no))
    page.locator("#submit").click()

    # expected url: http://localhost:{server_port}/submit_officer_images/officer/<id>
    officer_id = page.url.split("/")[-1]

    # 3. Submit an image
    page.goto(f"http://localhost:{server_port}/submit")
    page.locator("#department").select_option(dept_id)
    submit_image_to_dropzone(page, img_path)

    # 4. Classify the uploaded image
    page.goto(f"http://localhost:{server_port}/sort/departments/{dept_id}")

    # Check that image loaded correctly: https://stackoverflow.com/a/36296478
    image = page.locator("img.img-responsive")
    assert image.evaluate("image => image.complete") is True
    assert image.evaluate("image => image.naturalHeight") > 0

    page.locator("#answer-yes").click()
    expect_banner_with_text(page, "Updated image classification")
    expect(page.get_by_text("All images have been classified!")).to_be_visible()

    # 5. Identify the new officer in the uploaded image
    page.goto(f"http://localhost:{server_port}/cop_faces/departments/{dept_id}")
    page.locator("#officer_id").fill(str(officer_id))
    page.locator("input[value='Add identified face']").click()

    expect_banner_with_text(page, "Tag added to database")

    # 6. Log out as admin
    logout(page, server_port)

    # 7. Check that the tag appears on the officer page
    page.goto(f"http://localhost:{server_port}/officers/{officer_id}")
    page.locator("a > img.officer-face").click()

    # 8. Check that the tag frame is fully contained within the image
    page.locator("#face-tag-frame").wait_for(state="visible")

    image_box = page.locator("#face-img").bounding_box()
    frame_box = page.locator("#face-tag-frame").bounding_box()
    assert image_box["x"] <= frame_box["x"]
    assert image_box["y"] <= frame_box["y"]
    assert image_box["x"] + image_box["width"] >= frame_box["x"] + frame_box["width"]
    assert image_box["y"] + image_box["height"] >= frame_box["y"] + frame_box["height"]
    assert image_box["y"] <= frame_box["y"]


@skip("Continually fails, S3 mock seems wonky")
def test_anonymous_user_can_upload_image(page, server_port, session):
    test_dir = os.path.dirname(os.path.realpath(__file__))
    img_path = os.path.join(test_dir, "images/200Cat.jpeg")

    login_admin(page, server_port)

    # 1. Create new department as admin (to avoid mockdata)
    page.goto(f"http://localhost:{server_port}/departments/new")
    page.locator("#name").fill("Auburn Police Department")
    page.locator("#short_name").fill("APD")
    page.locator("#state").select_option("WA")
    page.locator("#submit").click()

    # 2. Log out
    logout(page, server_port)

    # 3. Upload image
    page.goto(f"http://localhost:{server_port}/submit")

    dept_select = page.locator("#department")
    dept_select.select_option(label="Auburn Police Department")
    dept_id = dept_select.evaluate("select => select.selectedOptions[0].value")

    submit_image_to_dropzone(page, img_path)

    # 4. Login as admin again
    login_admin(page, server_port)

    # 5. Check that there is 1 image to classify
    page.goto(f"http://localhost:{server_port}/sort/departments/{dept_id}")

    expect(
        page.get_by_text(
            "Do you see uniformed law enforcement officers in the photo below?"
        )
    ).to_be_visible()

    page.locator("#answer-yes").click()

    # 6. All images tagged!
    expect_banner_with_text(page, "Updated image classification")
    expect(page.get_by_text("All images have been classified!")).to_be_visible()
