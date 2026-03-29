from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({"width": 1260, "height": 800})
    page.goto('http://localhost:8000')
    page.wait_for_timeout(1000)
    page.screenshot(path='header_1260.png')

    page.set_viewport_size({"width": 1300, "height": 800})
    page.goto('http://localhost:8000')
    page.wait_for_timeout(1000)
    page.screenshot(path='header_1300.png')

    browser.close()
