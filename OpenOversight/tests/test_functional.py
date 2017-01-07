import time


def test_complainant_route(browser):
    browser.get("http://localhost:5000")
    assert "OpenOversight" in browser.title

    # stop server
    browser.get("http://localhost:5000/shutdown")
    time.sleep(3)
