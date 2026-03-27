import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Outbound email service.
    Replace with real SMTP / SendGrid / SES implementation for production.
    """

    async def send_verification_email(self, email: str, token: str) -> None:
        logger.info("[EMAIL] Verification → %s (token=%s...)", email, token[:8])

    async def send_welcome_email(self, email: str, username: str) -> None:
        logger.info("[EMAIL] Welcome → %s (user=%s)", email, username)

    async def send_password_reset_email(self, email: str, token: str) -> None:
        logger.info("[EMAIL] Password reset → %s (token=%s...)", email, token[:8])

    async def send_notification(self, email: str, subject: str, body: str) -> None:
        logger.info("[EMAIL] Notification → %s | %s", email, subject)


email_service = EmailService()
