"""
OCR Service — Gemini AI document extraction.
"""
import io
import json
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

    def _generate_json_from_image(self, prompt: str, image_bytes: bytes) -> Dict[str, Any]:
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        response = self.model.generate_content([prompt, image])
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        extracted = json.loads(text.strip())
        return extracted

    async def extract_id_front(self, front_image_bytes: bytes) -> Dict[str, Any]:
        """OCR national ID / document front (portrait side)."""
        if settings.GEMINI_OCR_MOCK:
            return _mock_id_result(
                ["GEMINI_OCR_MOCK=true: ID front OCR skipped; fill fields manually."]
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
            This is the FRONT side of an identity document (national ID, passport data page, or driver license front).

            Extract ONLY these fields from this image:
            - full_name: Full name as printed
            - date_of_birth: YYYY-MM-DD
            - document_type: passport, driver_license, or national_id
            - document_number: ID or document number
            - issue_date: YYYY-MM-DD if visible on this side
            - expiry_date: YYYY-MM-DD if visible on this side
            - nationality: Country or code
            - gender: M, F, or Other
            - place_of_birth: if visible

            Return ONLY a valid JSON object. Use null for missing fields.
            Include a top-level "confidence" field (0.0-1.0) for this extraction.
            """
            extracted = self._generate_json_from_image(prompt, front_image_bytes)
            conf = float(extracted.pop("confidence", 0.0))
            logger.info("ID front OCR completed with confidence: %s", conf)
            return {"success": True, "extracted": extracted, "confidence": conf}
        except Exception as e:
            logger.error("ID front OCR failed: %s", e)
            if settings.GEMINI_OCR_FALLBACK_MOCK_ON_QUOTA and _is_quota_or_rate_error(e):
                return _mock_id_result(
                    [
                        "ID front OCR: Gemini quota or rate limit — using empty extract. "
                        "Enable Generative Language API / billing in Google Cloud, or set GEMINI_OCR_MOCK=true."
                    ]
                )
            return {"success": False, "error": str(e), "extracted": {}, "confidence": 0.0}

    async def extract_id_back(self, back_image_bytes: bytes) -> Dict[str, Any]:
        """OCR national ID / document back (MRZ, barcode zone)."""
        if settings.GEMINI_OCR_MOCK:
            return _mock_id_result(
                ["GEMINI_OCR_MOCK=true: ID back OCR skipped; fill fields manually."]
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
            This is the BACK side of an identity document.

            Extract ONLY these fields:
            - document_number: if repeated or clearer here
            - expiry_date: YYYY-MM-DD if shown only on the back
            - issue_date: YYYY-MM-DD if shown only on the back
            - mrz_line1: First line of MRZ (Machine Readable Zone) if present
            - mrz_line2: Second line of MRZ if present
            - issuing_authority: if visible
            - full_name: only if clearly visible on this side (often MRZ encodes it)

            Return ONLY a valid JSON object. Use null for missing fields.
            Include a top-level "confidence" field (0.0-1.0) for this extraction.
            """
            extracted = self._generate_json_from_image(prompt, back_image_bytes)
            conf = float(extracted.pop("confidence", 0.0))
            logger.info("ID back OCR completed with confidence: %s", conf)
            return {"success": True, "extracted": extracted, "confidence": conf}
        except Exception as e:
            logger.error("ID back OCR failed: %s", e)
            if settings.GEMINI_OCR_FALLBACK_MOCK_ON_QUOTA and _is_quota_or_rate_error(e):
                return _mock_id_result(
                    [
                        "ID back OCR: Gemini quota or rate limit — using empty extract. "
                        "Enable Generative Language API / billing in Google Cloud, or set GEMINI_OCR_MOCK=true."
                    ]
                )
            return {"success": False, "error": str(e), "extracted": {}, "confidence": 0.0}

    async def extract_id_document(
        self, front_image_bytes: bytes, back_image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Legacy single call: run front + optional back and merge into one id_document blob.
        """
        from app.modules.kyc.application.services.ocr_merge import (
            average_id_confidence,
            merge_id_front_back,
        )

        front_res = await self.extract_id_front(front_image_bytes)
        back_res: Dict[str, Any] = {"success": True, "extracted": {}, "confidence": 0.0}
        if back_image_bytes:
            back_res = await self.extract_id_back(back_image_bytes)

        fe = dict(front_res.get("extracted") or {})
        be = dict(back_res.get("extracted") or {})
        merged_flat = merge_id_front_back(fe, be)
        id_conf = average_id_confidence(
            float(front_res.get("confidence") or 0.0),
            float(back_res.get("confidence") or 0.0) if back_image_bytes else None,
            bool(back_image_bytes),
        )
        merged_flat.pop("confidence", None)
        merged_flat["confidence"] = id_conf

        success = bool(front_res.get("success"))
        if back_image_bytes:
            success = success and bool(back_res.get("success"))
        warnings: List[str] = list(front_res.get("warnings") or [])
        warnings.extend(back_res.get("warnings") or [])

        err_msg = None
        if not success:
            err_msg = front_res.get("error") or back_res.get("error") or "ID OCR failed"

        return {
            "success": success,
            "extracted": merged_flat,
            "confidence": id_conf,
            "warnings": warnings,
            "id_front": fe,
            "id_back": be,
            "error": err_msg,
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

            extracted = self._generate_json_from_image(prompt, image_bytes)
            conf = float(extracted.pop("confidence", 0.0))

            logger.info(
                "Utility bill OCR completed with confidence: %s",
                conf,
            )

            return {
                "success": True,
                "extracted": extracted,
                "confidence": conf,
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
