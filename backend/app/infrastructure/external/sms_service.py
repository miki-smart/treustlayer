import logging

logger = logging.getLogger(__name__)


class SMSService:
    """
    Outbound SMS service.
    Replace with Twilio / AWS SNS implementation for production.
    """

    async def send_otp(self, phone_number: str, otp: str) -> None:
        logger.info("[SMS] OTP → %s : %s", phone_number, otp)

    async def send_notification(self, phone_number: str, message: str) -> None:
        logger.info("[SMS] Notification → %s : %s", phone_number, message[:50])


sms_service = SMSService()
