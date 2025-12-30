import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Testing Playwright Launch...")
    try:
        async with async_playwright() as p:
            print("Playwright started.")
            try:
                print("Attempting launch...")
                browser = await p.chromium.launch(headless=False)
                print("Browser launched successfully!")
                page = await browser.new_page()
                await page.goto("https://example.com")
                print("Navigated to example.com")
                await browser.close()
                print("Browser closed.")
            except Exception as e:
                print(f"Launch failed: {e}")
    except Exception as e:
        print(f"Playwright failed to start: {e}")

if __name__ == "__main__":
    asyncio.run(main())
