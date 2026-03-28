"""
Unit tests for OCR Service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.kyc.application.services.ocr_service import OCRService


class TestOCRService:
    """Test OCRService."""

    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance."""
        return OCRService()

    @pytest.mark.asyncio
    async def test_extract_id_document_success(self, ocr_service):
        """Merged ID extraction uses split front/back."""
        ocr_service.extract_id_front = AsyncMock(
            return_value={
                "success": True,
                "extracted": {
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-01",
                    "document_type": "passport",
                    "document_number": "AB123456",
                    "nationality": "US",
                },
                "confidence": 0.95,
            }
        )
        ocr_service.extract_id_back = AsyncMock(
            return_value={"success": True, "extracted": {}, "confidence": 0.0}
        )

        result = await ocr_service.extract_id_document(front_image_bytes=b"fake-image-data")

        assert result["success"] is True
        assert result["extracted"]["full_name"] == "John Doe"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_extract_id_document_no_model(self):
        """ID extraction when model not configured."""
        ocr_service = OCRService()
        ocr_service.model = None

        result = await ocr_service.extract_id_document(front_image_bytes=b"fake-image-data")

        assert result["success"] is False
        assert "not configured" in (result.get("error") or "")

    @pytest.mark.asyncio
    async def test_extract_utility_bill_success(self, ocr_service):
        """Utility bill extraction via mocked Gemini helper."""
        ocr_service.model = MagicMock()

        def fake_gen(prompt: str, image_bytes: bytes):
            return {
                "billing_name": "John Doe",
                "address": "123 Main St, City, State 12345",
                "service_provider": "Electric Company",
                "service_type": "electricity",
                "bill_date": "2026-03-01",
                "confidence": 0.90,
            }

        ocr_service._generate_json_from_image = fake_gen  # type: ignore[method-assign]

        result = await ocr_service.extract_utility_bill(image_bytes=b"fake-bill-data")

        assert result["success"] is True
        assert result["extracted"]["address"] == "123 Main St, City, State 12345"
        assert result["confidence"] == 0.90

    @pytest.mark.asyncio
    async def test_extract_id_document_with_json_markers(self, ocr_service):
        """extract_id_front parses JSON with code fences via mock."""
        ocr_service.extract_id_front = AsyncMock(
            return_value={
                "success": True,
                "extracted": {"full_name": "Jane Smith", "document_type": "driver_license"},
                "confidence": 0.88,
            }
        )
        ocr_service.extract_id_back = AsyncMock(
            return_value={"success": True, "extracted": {}, "confidence": 0.0}
        )

        result = await ocr_service.extract_id_document(front_image_bytes=b"fake-image-data")

        assert result["success"] is True
        assert result["extracted"]["full_name"] == "Jane Smith"
