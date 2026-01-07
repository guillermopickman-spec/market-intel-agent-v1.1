import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async
from core.logger import get_logger
from core.settings import settings
from services.document_service import ingest_document

logger = get_logger("ScraperService")

async def scrape_web(url: str, conversation_id: int = 0) -> str:
    """
    Async Scraper compatible with Windows (Proactor) and Linux (No-Sandbox).
    Enhanced with aggressive timeouts and better error handling.
    """
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Use a more aggressive timeout (30s instead of 60s for faster failure)
    timeout_seconds = min(settings.SCRAPER_TIMEOUT, 30)
    timeout_ms = timeout_seconds * 1000
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Helps with memory issues in Docker
                "--disable-gpu",  # Not needed in headless
                "--disable-software-rasterizer"
            ]
        )
        async with browser:
            try:
                # Set context timeout
                context = await browser.new_context(
                    user_agent=ua,
                    viewport={"width": 1920, "height": 1080}
                )
                context.set_default_timeout(timeout_ms)
                
                try:
                    page = await context.new_page()
                    page.set_default_timeout(timeout_ms)
                    await stealth_async(page)
                    
                    logger.info(f"🚀 Scraping: {url} (timeout: {timeout_seconds}s)")
                    
                    # Try domcontentloaded first (faster), fallback to commit if needed
                    try:
                        await asyncio.wait_for(
                            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms),
                            timeout=timeout_seconds
                        )
                    except (PlaywrightTimeoutError, asyncio.TimeoutError):
                        logger.warning(f"⏱️ domcontentloaded timeout, trying commit strategy for {url}")
                        try:
                            await asyncio.wait_for(
                                page.goto(url, wait_until="commit", timeout=15000),  # 15s for commit
                                timeout=15
                            )
                        except (PlaywrightTimeoutError, asyncio.TimeoutError):
                            logger.error(f"❌ Both navigation strategies failed for {url}")
                            return f"Error: Page navigation timed out after {timeout_seconds} seconds. The site may be blocking automated access or is too slow."
                    
                    # Wait a bit for dynamic content, but with timeout
                    try:
                        await asyncio.wait_for(asyncio.sleep(2), timeout=2)
                        await page.mouse.wheel(0, 500)
                        await asyncio.wait_for(asyncio.sleep(1), timeout=1)
                    except asyncio.TimeoutError:
                        pass  # Continue even if wait fails
                    
                    # Get text with timeout
                    try:
                        raw_text = await asyncio.wait_for(
                            page.inner_text("body"),
                            timeout=10
                        )
                        clean_text = re.sub(r'\n\s*\n', '\n', raw_text).strip()
                        
                        if len(clean_text) < 100:
                            logger.warning(f"⚠️ Very little content extracted from {url} ({len(clean_text)} chars)")
                            return f"Error: Page loaded but very little content extracted ({len(clean_text)} chars). Site may be blocking automated access."
                        
                        ingest_document(f"Scrape: {url}", clean_text[:5000], conversation_id)
                        logger.info(f"✅ Successfully scraped {url} ({len(clean_text)} chars)")
                        return clean_text
                    except asyncio.TimeoutError:
                        logger.error(f"❌ Text extraction timed out for {url}")
                        return f"Error: Text extraction timed out after 10 seconds"
                    
                finally:
                    await context.close()
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower() or "navigation timeout" in error_msg.lower():
                    logger.error(f"❌ Scrape timed out after {timeout_seconds}s: {url}")
                    return f"Error: Request timed out after {timeout_seconds} seconds. The site may be blocking automated access."
                logger.error(f"❌ Scrape failed: {error_msg}")
                return f"Error: {error_msg}"
