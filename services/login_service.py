from playwright.sync_api import sync_playwright
from core.logger import get_logger

logger = get_logger("LoginService")

def automate_login_test():
    """
    Script to automate login on a test website.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        try:
            context = browser.new_context()
            try:
                page = context.new_page()
                
                try:
                    logger.info("Visiting login page...")
                    page.goto("https://the-internet.herokuapp.com/login")

                    page.fill("#username", "tomsmith")
                    page.fill("#password", "SuperSecretPassword!")
                    page.click("button[type='submit']")
                    page.wait_for_load_state("networkidle")

                    success_msg = page.inner_text("#flash")
                    page.wait_for_timeout(3000)
                    
                    if "You logged into a secure area!" in success_msg:
                        return "✅ Login successful: We're in!"
                    else:
                        return "❌ Login failed or the message changed."
                except Exception as e:
                    return f"Error in automation: {str(e)}"
                finally:
                    page.close()
            finally:
                context.close()
        except Exception as e:
            return f"Error initializing browser: {str(e)}"
        finally:
            browser.close()