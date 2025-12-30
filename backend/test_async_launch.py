import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting Playwright...")
    async with async_playwright() as p:
        print("Launching Browser...")
        try:
            browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
            print("Browser Launched!")
            context = await browser.new_context(no_viewport=True)
            page = await context.new_page()
            print("Page Created!")
            await page.goto("https://example.com")
            print("Navigated to Example.com")
            await asyncio.sleep(5)
            await browser.close()
            print("Browser Closed.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
