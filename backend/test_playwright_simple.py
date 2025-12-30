from playwright.sync_api import sync_playwright
import time

print("Starting Playwright test...")
try:
    with sync_playwright() as p:
        print("Playwright started.")
        browser = p.chromium.launch(headless=False)
        print("Browser launched.")
        page = browser.new_page()
        print("Page created.")
        page.goto("https://example.com")
        print(f"Page title: {page.title()}")
        browser.close()
        print("Browser closed.")
except Exception as e:
    print(f"ERROR: {e}")
