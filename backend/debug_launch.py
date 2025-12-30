import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("http://example.com")
        print(await page.title())
        await browser.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
