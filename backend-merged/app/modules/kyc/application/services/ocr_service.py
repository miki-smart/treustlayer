"""
OCR Service — Gemini AI document extraction.
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_quota_or_rate_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "429" in msg or "quota" in msg or "resource exhausted" in msg:
        return True
    name = type(exc).__name__
    return name in ("ResourceExhausted", "TooManyRequests")


def _mock_id_result(warnings: List[str]) -> Dict[str, Any]:
    return {
        "success": True,
        "extracted": {},
        "confidence": 0.0,
        "mock": True,
        "warnings": warnings,
    }


def _mock_utility_result(warnings: List[str]) -> Dict[str, Any]:
    return {
        "success": True,
        "extracted": {},
        "confidence": 0.0,
        "mock": True,
        "warnings": warnings,
    }


class OCRService:
    """
    OCR service using Google Gemini AI.

    Extracts structured data from ID documents and utility bills.
    """

    def __init__(self):
        self.model = None
        if settings.GEMINI_OCR_MOCK:
            logger.info("GEMINI_OCR_MOCK=true — Gemini will not be called")
            return
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured, OCR will be disabled")
            return
        try:
            import google.generativeai as genai
        except ImportError as exc:
            logger.warning(
                "google-generativeai is not installed (%s); OCR disabled. "
                "Install with: pip install google-generativeai",
                exc,
            )
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def extract_id_document(
        self, front_image_bytes: bytes, back_image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        if settings.GEMINI_OCR_MOCK:
            return _mock_id_result(
                ["GEMINI_OCR_MOCK=true: ID OCR skipped; fill fields manually."]
            )

        if not self.model:
            return {
                "success": False,
                "error": "OCR service not configured",
                "extracted": {},
                "confidence": 0.0,
            }

        try:
            prompt = """
            Extract the following information from this ID document image:

            - full_name: Full name as it appears on the document
            - date_of_birth: Date of birth (YYYY-MM-DD format)
            - document_type: Type of document (passport, driver_license, national_id)
            - document_number: Document number or ID number
            - issue_date: Issue date (YYYY-MM-DD format)
            - expiry_date: Expiry date (YYYY-MM-DD format)
            - nationality: Nationality or country code
            - gender: Gender (M/F/Other)
            - place_of_birth: Place of birth (if available)
            - mrz_line1: First line of MRZ (Machine Readable Zone) if present
            - mrz_line2: Second line of MRZ if present

            Return ONLY a valid JSON object with these fields. Use null for missing fields.
            Include a "confidence" field (0.0-1.0) indicating extraction confidence.
            """

            from PIL import Image
            import io
            import json

            front_image = Image.open(io.BytesIO(front_image_bytes))

            response = self.model.generate_content([prompt, front_image])

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            extracted = json.loads(text.strip())

            logger.info(
                "ID document OCR completed with confidence: %s",
                extracted.get("confidence", 0),
            )

            return {
                "success": True,
                "extracted": extracted,
                "confidence": extracted.get("confidence", 0.0),
            }

        except Exception as e:
            logger.error("OCR extraction failed: %s", e)
            if settings.GEMINI_OCR_FALLBACK_MOCK_ON_QUOTA and _is_quota_or_rate_error(e):
                return _mock_id_result(
                    [
                        "ID OCR: Gemini quota or rate limit — using empty extract. "
                        "Enable Generative Language API / billing in Google Cloud, or set GEMINI_OCR_MOCK=true."
                    ]
                )
            return {
                "success": False,
                "error": str(e),
                "extracted": {},
                "confidence": 0.0,
            }

    async def extract_utility_bill(self, image_bytes: bytes) -> Dict[str, Any]:
        if settings.GEMINI_OCR_MOCK:
            return _mock_utility_result(
                ["GEMINI_OCR_MOCK=true: utility bill OCR skipped; fill fields manually."]
            )

        if not self.model:
            return {
                "success": False,
                "error": "OCR service not configured",
                "extracted": {},
                "confidence": 0.0,
            }

        try:
            prompt = """
            Extract the following information from this utility bill image:

            - billing_name: Name on the bill
            - address: Full address
            - service_provider: Utility company name
            - service_type: Type of service (electricity, water, gas, internet, etc.)
            - bill_date: Bill date (YYYY-MM-DD format)
            - account_number: Account number (if visible)

            Return ONLY a valid JSON object with these fields. Use null for missing fields.
            Include a "confidence" field (0.0-1.0) indicating extraction confidence.
            """

            from PIL import Image
            import io
            import json

            image = Image.open(io.BytesIO(image_bytes))

            response = self.model.generate_content([prompt, image])

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            extracted = json.loads(text.strip())

            logger.info(
                "Utility bill OCR completed with confidence: %s",
                extracted.get("confidence", 0),
            )

            return {
                "success": True,
                "extracted": extracted,
                "confidence": extracted.get("confidence", 0.0),
            }

        except Exception as e:
            logger.error("Utility bill OCR extraction failed: %s", e)
            if settings.GEMINI_OCR_FALLBACK_MOCK_ON_QUOTA and _is_quota_or_rate_error(e):
                return _mock_utility_result(
                    [
                        "Utility bill OCR: Gemini quota or rate limit — using empty extract. "
                        "Enable Generative Language API / billing in Google Cloud, or set GEMINI_OCR_MOCK=true."
                    ]
                )
            return {
                "success": False,
                "error": str(e),
                "extracted": {},
                "confidence": 0.0,
            }
