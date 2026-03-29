import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # We need a local web server to serve the page properly.
        # Assuming php -S is running on port 8000
        await page.goto("http://localhost:8000/index.html")

        # Test sizes around the breakpoint
        widths = [992, 1060, 1200, 1250, 1300, 1350, 1400]

        os.makedirs("verification/screenshots", exist_ok=True)

        for width in widths:
            await page.set_viewport_size({"width": width, "height": 900})
            await asyncio.sleep(0.5)  # Wait for resize to take effect
            await page.screenshot(path=f"verification/screenshots/verification_{width}.png", full_page=False)
            print(f"Captured screenshot at {width}px width")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
