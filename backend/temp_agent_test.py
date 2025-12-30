import pytest
from playwright.async_api import async_playwright, Playwright, Page, Error

@pytest.mark.asyncio
async def test_scenario():
    """
    This script automates the process of searching for a product on Flipkart,
    sorting the results, selecting the first item, and adding it to the cart.
    """
    async with async_playwright() as p:
        # 1. Browser Launch and Context Creation (as per requirements)
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
        context = await browser.new_context(viewport=None)
        page = await context.new_page()

        # 2. Navigate to Flipkart homepage
        target_url = "https://www.flipkart.com/"
        await page.goto(target_url)

        # 3. Handle potential login popup
        try:
            # This selector targets the '✕' close button of the login modal.
            login_popup_close_button = page.locator("button", has_text="✕")
            await login_popup_close_button.wait_for(state="visible", timeout=5000)
            await login_popup_close_button.click()
            print("Login popup found and closed.")
        except Error:
            # This will be raised if the popup doesn't appear within the timeout.
            print("Login popup did not appear or was not found.")

        # 4. Type 'office adjustable table' into the search bar
        search_bar_selector = '[name="q"]'
        search_term = 'office adjustable table'
        await page.wait_for_selector(search_bar_selector, timeout=5000)
        await page.locator(search_bar_selector).fill(search_term)

        # 5. Press the 'Enter' key on the keyboard
        await page.keyboard.press('Enter')
        print(f"Searched for: '{search_term}'")

        # 6. Sort by "Price -- Low to High"
        sort_option_selector = "div:text-is('Price -- Low to High')"
        await page.wait_for_selector(sort_option_selector, timeout=5000)
        await page.locator(sort_option_selector).click()
        print("Sorted by 'Price -- Low to High'.")
        
        # Wait for the URL to update to confirm the sort has been applied
        await page.wait_for_url("**/sort=price_asc**", timeout=5000)
        print("URL confirmed sort parameter.")

        # 7. Click on the first available product link
        # This selector targets the first product link in the search results.
        # It's designed to be robust against different view layouts.
        first_product_selector = "a[target='_blank'][rel='noopener noreferrer']"
        
        # Wait for at least one product to be visible
        await page.wait_for_selector(first_product_selector, timeout=5000)

        # Use a context manager to handle the new page/tab that opens
        async with context.expect_page() as new_page_info:
            await page.locator(first_product_selector).first.click()
        
        product_page = await new_page_info.value
        await product_page.wait_for_load_state()
        print(f"Clicked on the first product. New page URL: {product_page.url}")

        # 8. Add to cart
        # This selector targets the "Add to cart" button on the product page.
        add_to_cart_selector = "//button[text()='Add to cart']"
        await product_page.wait_for_selector(add_to_cart_selector, timeout=5000)
        await product_page.locator(add_to_cart_selector).click()
        print("Clicked 'Add to cart'.")
        
        # A brief pause to allow visual confirmation before the script ends.
        await product_page.wait_for_timeout(3000)

        # Clean up
        await context.close()
        await browser.close()
        print("Test completed and browser closed.")