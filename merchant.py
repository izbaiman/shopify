import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def get_amazon_products(merchant_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Headless=False helps avoid detection
        page = await browser.new_page()
        
        # Apply stealth to hide that we are a bot
        await stealth_async(page)
        
        # Construct the merchant URL
        url = f"https://www.amazon.com/s?me={merchant_id}"
        
        await page.goto(url)
        await page.wait_for_timeout(2000) # Wait for page to load

        products = []

        while True:
            # Find all product containers
            items = await page.query_selector_all('div[data-component-type="s-search-result"]')
            
            for item in items:
                title_el = await item.query_selector('h2 span')
                price_el = await item.query_selector('.a-price-whole')
                
                title = await title_el.inner_text() if title_el else "No Title"
                price = await price_el.inner_text() if price_el else "N/A"
                
                print(f"Product: {title} | Price: {price}")
                products.append({"title": title, "price": price})

            # Check if there is a "Next" page button
            next_button = await page.query_selector('a.s-pagination-next')
            if next_button:
                await next_button.click()
                await page.wait_for_timeout(3000) # Pause to look human
            else:
                break # No more pages

        await browser.close()
        return products

# Use the Merchant ID here
merchant_id = "A1Q1QW8HP0UOI1" 
asyncio.run(get_amazon_products(merchant_id))