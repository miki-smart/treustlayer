"""
Email service stub.

In production, integrate with SMTP or a service like SendGrid.
For now, logs emails to console.
"""
import logging

logger = logging.getLogger(__name__)


class EmailService:
    async def send_verification_email(self, to_email: str, token: str) -> None:
        """Send email verification link."""
        logger.info(
            "📧 [EMAIL] Verification email to %s | Token: %s",
            to_email,
            token[:8] + "...",
        )
        logger.info("   Link: http://localhost:5173/verify-email?token=%s", token)

    async def send_password_reset_email(self, to_email: str, token: str) -> None:
        """Send password reset link."""
        logger.info(
            "📧 [EMAIL] Password reset email to %s | Token: %s",
            to_email,
            token[:8] + "...",
        )
        logger.info("   Link: http://localhost:5173/reset-password?token=%s", token)


email_service = EmailService()
