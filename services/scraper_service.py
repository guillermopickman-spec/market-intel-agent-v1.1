import re
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from core.logger import get_logger
from core.settings import settings
from services.document_service import ingest_document

logger = get_logger("ScraperService")

async def scrape_web(url: str, conversation_id: int = 0) -> str:
    """
    Async Scraper compatible with Windows (Proactor) and Linux (No-Sandbox).
    """
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        async with browser:
            try:
                context = await browser.new_context(user_agent=ua)
                try:
                    page = await context.new_page()
                    await stealth_async(page)
                    
                    logger.info(f"🚀 Scraping: {url}")
                    timeout_ms = settings.SCRAPER_TIMEOUT * 1000
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    
                    await page.mouse.wheel(0, 500)
                    await asyncio.sleep(1)

                    raw_text = await page.inner_text("body")
                    clean_text = re.sub(r'\n\s*\n', '\n', raw_text).strip()

                    ingest_document(f"Scrape: {url}", clean_text[:5000], conversation_id)
                    
                    return clean_text
                finally:
                    await context.close()
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "navigation timeout" in error_msg.lower():
                    logger.error(f"❌ Scrape timed out after {settings.SCRAPER_TIMEOUT}s: {url}")
                    return f"Error: Request timed out after {settings.SCRAPER_TIMEOUT} seconds"
                logger.error(f"❌ Scrape failed: {error_msg}")
                return f"Error: {error_msg}"