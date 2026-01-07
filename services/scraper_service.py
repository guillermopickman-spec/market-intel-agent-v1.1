import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async
from core.logger import get_logger
from core.settings import settings
from services.document_service import ingest_document

logger = get_logger("ScraperService")

async def _scrape_web_internal(url: str, conversation_id: int = 0) -> str:
    """
    Internal scraper function - wrapped with timeout in main function.
    """
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    timeout_seconds = min(settings.SCRAPER_TIMEOUT, 30)
    timeout_ms = timeout_seconds * 1000
    
    # Wrap Playwright initialization in timeout to prevent hangs in Render
    try:
        playwright_manager = async_playwright()
        p = await asyncio.wait_for(playwright_manager.__aenter__(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.error("❌ Playwright initialization timed out (10s)")
        return "Error: Browser initialization timed out. Playwright may not be properly configured in this environment."
    except Exception as e:
        logger.error(f"❌ Playwright initialization failed: {str(e)}")
        return f"Error: Failed to initialize browser - {str(e)}"
    
    try:
        # Wrap browser launch in timeout to prevent hangs
        try:
            browser = await asyncio.wait_for(
                p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-software-rasterizer",
                        "--disable-background-networking",
                        "--disable-background-timer-throttling",
                        "--disable-renderer-backgrounding",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-ipc-flooding-protection",
                        "--single-process",  # Critical for Render - reduces resource usage
                    ]
                ),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("❌ Browser launch timed out (15s)")
            await playwright_manager.__aexit__(None, None, None)
            return "Error: Browser launch timed out. The environment may not have sufficient resources."
        except Exception as e:
            logger.error(f"❌ Browser launch failed: {str(e)}")
            await playwright_manager.__aexit__(None, None, None)
            return f"Error: Browser launch failed - {str(e)}"
        
        try:
            context = await browser.new_context(
                user_agent=ua,
                viewport={"width": 1920, "height": 1080}
            )
            context.set_default_timeout(timeout_ms)
            
            try:
                page = await context.new_page()
                page.set_default_timeout(timeout_ms)
                
                # Wrap stealth_async in timeout - this can hang
                try:
                    await asyncio.wait_for(stealth_async(page), timeout=5)
                except asyncio.TimeoutError:
                    logger.warning("⚠️ stealth_async timed out, continuing without stealth")
                
                logger.info(f"🚀 Scraping: {url} (timeout: {timeout_seconds}s)")
                
                # Try domcontentloaded first (faster)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                except PlaywrightTimeoutError:
                    logger.warning(f"⏱️ domcontentloaded timeout, trying commit strategy for {url}")
                    try:
                        await page.goto(url, wait_until="commit", timeout=15000)
                    except PlaywrightTimeoutError:
                        logger.error(f"❌ Both navigation strategies failed for {url}")
                        return f"Error: Page navigation timed out after {timeout_seconds} seconds. The site may be blocking automated access or is too slow."
                
                # Wait a bit for dynamic content
                await asyncio.sleep(1)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(1)
                
                # Get text
                raw_text = await page.inner_text("body")
                clean_text = re.sub(r'\n\s*\n', '\n', raw_text).strip()
                
                if len(clean_text) < 100:
                    logger.warning(f"⚠️ Very little content extracted from {url} ({len(clean_text)} chars)")
                    return f"Error: Page loaded but very little content extracted ({len(clean_text)} chars). Site may be blocking automated access."
                
                ingest_document(f"Scrape: {url}", clean_text[:5000], conversation_id)
                logger.info(f"✅ Successfully scraped {url} ({len(clean_text)} chars)")
                return clean_text
                
            finally:
                await context.close()
        except PlaywrightTimeoutError as e:
            logger.error(f"❌ Playwright timeout: {str(e)}")
            return f"Error: Request timed out after {timeout_seconds} seconds. The site may be blocking automated access."
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Scrape failed: {error_msg}")
            return f"Error: {error_msg}"
        finally:
            try:
                await browser.close()
            except:
                pass
    finally:
        try:
            await playwright_manager.__aexit__(None, None, None)
        except:
            pass

async def scrape_web(url: str, conversation_id: int = 0) -> str:
    """
    Async Scraper with top-level timeout wrapper to prevent infinite hangs.
    This ensures the function ALWAYS returns within the timeout period.
    """
    timeout_seconds = min(settings.SCRAPER_TIMEOUT, 30)
    
    try:
        # Wrap entire operation in timeout - this is the key fix
        result = await asyncio.wait_for(
            _scrape_web_internal(url, conversation_id),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"❌ Scrape operation timed out after {timeout_seconds}s: {url}")
        return f"Error: Scrape operation timed out after {timeout_seconds} seconds. The site may be blocking automated access or is too slow."
    except Exception as e:
        logger.error(f"❌ Unexpected error in scrape_web: {str(e)}")
        return f"Error: {str(e)}"
