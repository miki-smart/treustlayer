"""
Unit tests for OCR Service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.kyc.application.services.ocr_service import OCRService


class TestOCRService:
    """Test OCRService."""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance."""
        return OCRService()
    
    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_extract_id_document_success(self, mock_model_class, ocr_service):
        """Test successful ID document extraction."""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "document_type": "passport",
            "document_number": "AB123456",
            "nationality": "US",
            "confidence": 0.95
        }
        '''
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        ocr_service.model = mock_model
        
        result = await ocr_service.extract_id_document(
            front_image_bytes=b"fake-image-data"
        )
        
        assert result["success"] is True
        assert result["extracted"]["full_name"] == "John Doe"
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_extract_id_document_no_model(self):
        """Test ID extraction when model not configured."""
        ocr_service = OCRService()
        ocr_service.model = None
        
        result = await ocr_service.extract_id_document(
            front_image_bytes=b"fake-image-data"
        )
        
        assert result["success"] is False
        assert "not configured" in result["error"]
    
    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_extract_utility_bill_success(self, mock_model_class, ocr_service):
        """Test successful utility bill extraction."""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "billing_name": "John Doe",
            "address": "123 Main St, City, State 12345",
            "service_provider": "Electric Company",
            "service_type": "electricity",
            "bill_date": "2026-03-01",
            "confidence": 0.90
        }
        '''
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        ocr_service.model = mock_model
        
        result = await ocr_service.extract_utility_bill(image_bytes=b"fake-bill-data")
        
        assert result["success"] is True
        assert result["extracted"]["address"] == "123 Main St, City, State 12345"
        assert result["confidence"] == 0.90
    
    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_extract_id_document_with_json_markers(self, mock_model_class, ocr_service):
        """Test extraction with JSON code block markers."""
        mock_response = MagicMock()
        mock_response.text = '''```json
        {
            "full_name": "Jane Smith",
            "document_type": "driver_license",
            "confidence": 0.88
        }
        ```'''
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        ocr_service.model = mock_model
        
        result = await ocr_service.extract_id_document(
            front_image_bytes=b"fake-image-data"
        )
        
        assert result["success"] is True
        assert result["extracted"]["full_name"] == "Jane Smith"
