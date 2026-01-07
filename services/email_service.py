import resend
from typing import cast
from core.settings import settings
from core.logger import get_logger

logger = get_logger("EmailService")

class EmailService:
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        if self.api_key:
            resend.api_key = self.api_key

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """
        Sends an automated email via Resend.
        Pylance-safe version using type casting for Resend SendParams.
        Note: Resend SDK doesn't support direct timeout configuration,
        but the underlying HTTP client should respect system timeouts.
        """
        if not self.api_key:
            logger.error("Missing RESEND_API_KEY")
            return False

        try:
            email_params = {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "text": content,
            }

            resend.Emails.send(cast(resend.Emails.SendParams, email_params))
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                logger.error(f"Email service timed out while sending to {to_email}")
            else:
                logger.error(f"Email Service Error: {e}", exc_info=True)
            return False