import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        await page.goto("http://localhost:3000/")
        await asyncio.sleep(2)
        await page.screenshot(path="terminal_screenshot.png")
        print("Took screenshot of terminal")

        # Enable Admin Mode (Ctrl+Shift+A)
        await page.keyboard.press("Control+Shift+A")
        await asyncio.sleep(1)

        # Click on Strategies page
        # Open Legacy section first if needed
        # We need to click the 'Legacy' section header to reveal 'Strategies'
        await page.evaluate("Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Legacy')).click()")
        await asyncio.sleep(1)
        
        await page.evaluate("document.querySelector('button[aria-label=\"Strategies\"]').click()")
        await asyncio.sleep(1)
        await page.screenshot(path="strategies_screenshot.png")
        print("Took screenshot of strategies")

        # Click on Signals page
        await page.evaluate("document.querySelector('button[aria-label=\"Signals (Legacy)\"]').click()")
        await asyncio.sleep(1)
        await page.screenshot(path="signals_screenshot.png")
        print("Took screenshot of signals")

        # Click on News page
        await page.evaluate("document.querySelector('button[aria-label=\"News\"]').click()")
        await asyncio.sleep(1)
        await page.screenshot(path="news_screenshot.png")
        print("Took screenshot of news")
        
        # Click on Execution page
        await page.evaluate("document.querySelector('button[aria-label=\"Execution\"]').click()")
        await asyncio.sleep(1)
        await page.screenshot(path="execution_screenshot.png")
        print("Took screenshot of execution")

        # Click on Memory page
        await page.evaluate("document.querySelector('button[aria-label=\"Memory\"]').click()")
        await asyncio.sleep(1)
        await page.screenshot(path="memory_screenshot.png")
        print("Took screenshot of memory")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
