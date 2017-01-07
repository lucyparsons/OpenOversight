import time


def test_user_can_load_homepage_and_get_to_form(mockdata, browser):
    browser.get("http://localhost:5000")

    # Complainant loads homepage
    assert "OpenOversight" in browser.title
    browser.find_element_by_link_text("Try it").click()
    time.sleep(5)
    assert "Find an Officer" in browser.page_source


def test_user_can_use_form_to_get_to_gallery(mockdata, browser):
    browser.get("http://localhost:5000/find")

    # Complainant submits default search params and gets list of officers
    browser.find_element_by_name("submit-officer-search-form").click()
    time.sleep(10)
    assert "Digital Gallery" in browser.page_source


def test_user_can_get_to_complaint(mockdata, browser):
    browser.get("http://localhost:5000/complaint?officer_star=6265&officer_first_name=IVANA&officer_last_name=SNOTBALL&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png")

    time.sleep(3)
    # Complainant arrives at page with the badge number, name, and link
    # to complaint form
    assert "File a Complaint" in browser.page_source
