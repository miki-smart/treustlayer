"""
Gemini-powered OCR service for eKYC document extraction.

Supports:
  - National ID (front image + back image)
  - Utility Bill / Proof of Address

The service sends each document to Gemini's multimodal API with a strict JSON
extraction prompt and returns a structured OCRExtractedData object.

Environment variables:
  GEMINI_API_KEY   — Google AI Studio API key
  GEMINI_MODEL     — model name (default: gemini-2.0-flash)
"""

import asyncio
import json
import logging
from functools import partial

from google import genai
from google.genai import types as genai_types

from app.config import settings
from app.schemas.ocr import NationalIDData, UtilityBillData, OCRExtractedData

logger = logging.getLogger(__name__)

# ── Prompts ──────────────────────────────────────────────────────────────────

_ID_PROMPT = """
You are an expert OCR system specialised in extracting identity information
from government-issued National ID documents for financial KYC compliance.

I am providing you with the FRONT and BACK images of a National ID card.
Extract every piece of information that is clearly visible and return it as a
single valid JSON object. Use null for any field that is absent or illegible.
Dates must be in YYYY-MM-DD format. Do NOT include any text outside the JSON.

Required JSON schema:
{
  "full_name":      "string or null",
  "date_of_birth":  "YYYY-MM-DD or null",
  "id_number":      "string or null",
  "gender":         "Male | Female | Other | null",
  "nationality":    "string or null",
  "place_of_birth": "string or null",
  "issue_date":     "YYYY-MM-DD or null",
  "expiry_date":    "YYYY-MM-DD or null",
  "address":        "full residential address or null",
  "mrz_line1":      "MRZ line 1 verbatim or null",
  "mrz_line2":      "MRZ line 2 verbatim or null",
  "confidence":     0.0-1.0
}
"""

_UTILITY_PROMPT = """
You are an expert OCR system specialised in extracting address verification
information from utility bills and proof-of-address documents for financial
KYC compliance.

I am providing you with an image of a Utility Bill or Proof of Address.
Extract every piece of information that is clearly visible and return it as a
single valid JSON object. Use null for any field that is absent or illegible.
Dates must be in YYYY-MM-DD format. Do NOT include any text outside the JSON.

Required JSON schema:
{
  "billing_name":    "account holder name or null",
  "billing_address": "full billing address or null",
  "service_provider":"utility company name or null",
  "service_type":    "electricity | water | gas | internet | phone | other | null",
  "bill_date":       "YYYY-MM-DD or null",
  "account_number":  "account or customer number or null",
  "amount_due":      "amount with currency or null",
  "confidence":      0.0-1.0
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file to enable OCR document extraction."
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _parse_json_response(text: str) -> dict:
    """Strip markdown fences (```json … ```) and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        inner = parts[1].strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        text = inner
    return json.loads(text)


def _image_part(data: bytes, mime_type: str) -> genai_types.Part:
    return genai_types.Part.from_bytes(data=data, mime_type=mime_type)


def _sync_extract_id(
    front_bytes: bytes,
    front_mime: str,
    back_bytes: bytes,
    back_mime: str,
) -> NationalIDData:
    """Blocking call — run via executor to avoid blocking the event loop."""
    client = _get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            _ID_PROMPT,
            _image_part(front_bytes, front_mime),
            _image_part(back_bytes, back_mime),
        ],
    )
    raw = _parse_json_response(response.text)
    return NationalIDData(**{k: raw.get(k) for k in NationalIDData.model_fields})


def _sync_extract_utility(bill_bytes: bytes, bill_mime: str) -> UtilityBillData:
    """Blocking call — run via executor to avoid blocking the event loop."""
    client = _get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            _UTILITY_PROMPT,
            _image_part(bill_bytes, bill_mime),
        ],
    )
    raw = _parse_json_response(response.text)
    return UtilityBillData(**{k: raw.get(k) for k in UtilityBillData.model_fields})


# ── Public async API ──────────────────────────────────────────────────────────

async def extract_documents(
    id_front_bytes: bytes,
    id_front_mime: str,
    id_back_bytes: bytes,
    id_back_mime: str,
    utility_bytes: bytes,
    utility_mime: str,
) -> OCRExtractedData:
    """
    Send National ID (front + back) and Utility Bill to Gemini concurrently.
    Merges results into a single OCRExtractedData object.
    Raises ValueError if GEMINI_API_KEY is missing.
    Raises RuntimeError on any Gemini API or JSON parse failure.
    """
    loop = asyncio.get_event_loop()

    try:
        id_task = loop.run_in_executor(
            None,
            partial(_sync_extract_id, id_front_bytes, id_front_mime, id_back_bytes, id_back_mime),
        )
        util_task = loop.run_in_executor(
            None,
            partial(_sync_extract_utility, utility_bytes, utility_mime),
        )
        id_data, util_data = await asyncio.gather(id_task, util_task)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON response: %s", exc)
        raise RuntimeError("OCR extraction failed: model returned malformed JSON.") from exc
    except Exception as exc:
        logger.error("Gemini OCR error: %s", exc)
        raise RuntimeError(f"OCR extraction failed: {exc}") from exc

    # Utility bill address takes priority over ID address for proof-of-address
    resolved_address = util_data.billing_address or id_data.address
    overall = round((id_data.confidence + util_data.confidence) / 2, 3)

    return OCRExtractedData(
        # Identity
        full_name=id_data.full_name,
        date_of_birth=id_data.date_of_birth,
        id_number=id_data.id_number,
        gender=id_data.gender,
        nationality=id_data.nationality,
        place_of_birth=id_data.place_of_birth,
        issue_date=id_data.issue_date,
        expiry_date=id_data.expiry_date,
        mrz_line1=id_data.mrz_line1,
        mrz_line2=id_data.mrz_line2,
        # Address
        address=resolved_address,
        # Utility
        billing_name=util_data.billing_name,
        service_provider=util_data.service_provider,
        service_type=util_data.service_type,
        bill_date=util_data.bill_date,
        account_number=util_data.account_number,
        # Scores
        id_ocr_confidence=id_data.confidence,
        utility_ocr_confidence=util_data.confidence,
        overall_confidence=overall,
        documents_processed=["National ID (front)", "National ID (back)", "Utility Bill"],
    )
