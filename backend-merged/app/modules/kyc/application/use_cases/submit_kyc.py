"""
SubmitKYCUseCase — submit KYC documents with OCR extraction.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.identity.domain.repositories.user_repository import UserRepository
from app.modules.kyc.domain.entities.kyc_verification import KYCVerification, KYCStatus, KYCTier
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.kyc.application.services.file_storage_service import FileStorageService
from app.modules.kyc.application.services.ocr_service import OCRService

logger = logging.getLogger(__name__)


class SubmitKYCUseCase:
    """
    Submit KYC documents for verification.
    
    Steps:
    1. Validate user exists
    2. Save uploaded files
    3. Run OCR extraction
    4. Create KYC verification record
    5. Calculate initial risk score
    """
    
    def __init__(
        self,
        kyc_repo: KYCRepository,
        user_repo: UserRepository,
        file_storage: FileStorageService,
        ocr_service: OCRService,
    ):
        self.kyc_repo = kyc_repo
        self.user_repo = user_repo
        self.file_storage = file_storage
        self.ocr_service = ocr_service
    
    async def execute(
        self,
        user_id: str,
        id_front_bytes: bytes,
        id_back_bytes: Optional[bytes],
        utility_bill_bytes: bytes,
        face_image_bytes: bytes,
    ) -> KYCVerification:
        """
        Submit KYC documents.
        
        Args:
            user_id: User ID
            id_front_bytes: Front of ID document
            id_back_bytes: Back of ID document (optional)
            utility_bill_bytes: Utility bill image
            face_image_bytes: Face photo
        
        Returns:
            KYCVerification entity
        
        Raises:
            NotFoundError: User not found
            BadRequestError: Invalid input or existing KYC
        """
        # 1. Validate user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # 2. Check if KYC already exists
        existing_kyc = await self.kyc_repo.get_by_user_id(user_id)
        if existing_kyc and existing_kyc.status == KYCStatus.APPROVED:
            raise BadRequestError("KYC already approved for this user")
        
        # 3. Save files
        id_front_url = await self.file_storage.save_file(
            id_front_bytes, user_id, "id_front", "jpg"
        )
        
        id_back_url = None
        if id_back_bytes:
            id_back_url = await self.file_storage.save_file(
                id_back_bytes, user_id, "id_back", "jpg"
            )
        
        utility_bill_url = await self.file_storage.save_file(
            utility_bill_bytes, user_id, "utility_bill", "jpg"
        )
        
        face_image_url = await self.file_storage.save_file(
            face_image_bytes, user_id, "face_image", "jpg"
        )
        
        # 4. Run OCR extraction
        id_ocr_result = await self.ocr_service.extract_id_document(
            id_front_bytes, id_back_bytes
        )
        
        utility_ocr_result = await self.ocr_service.extract_utility_bill(utility_bill_bytes)
        
        # 5. Create KYC verification record
        id_data = id_ocr_result.get("extracted", {})
        utility_data = utility_ocr_result.get("extracted", {})
        
        kyc = KYCVerification(
            user_id=user_id,
            status=KYCStatus.PENDING,
            tier=KYCTier.TIER_0,
            full_name=id_data.get("full_name"),
            date_of_birth=self._parse_date(id_data.get("date_of_birth")),
            gender=id_data.get("gender"),
            nationality=id_data.get("nationality"),
            place_of_birth=id_data.get("place_of_birth"),
            document_type=id_data.get("document_type"),
            document_number=id_data.get("document_number"),
            issue_date=self._parse_date(id_data.get("issue_date")),
            expiry_date=self._parse_date(id_data.get("expiry_date")),
            address=utility_data.get("address"),
            billing_name=utility_data.get("billing_name"),
            service_provider=utility_data.get("service_provider"),
            service_type=utility_data.get("service_type"),
            bill_date=self._parse_date(utility_data.get("bill_date")),
            account_number=utility_data.get("account_number"),
            mrz_line1=id_data.get("mrz_line1"),
            mrz_line2=id_data.get("mrz_line2"),
            id_front_url=id_front_url,
            id_back_url=id_back_url,
            utility_bill_url=utility_bill_url,
            face_image_url=face_image_url,
            documents_submitted=["id_front", "utility_bill", "face_image"]
            + (["id_back"] if id_back_bytes else []),
            extracted_data={
                "id_document": id_data,
                "utility_bill": utility_data,
            },
            id_ocr_confidence=id_ocr_result.get("confidence", 0.0),
            utility_ocr_confidence=utility_ocr_result.get("confidence", 0.0),
            overall_confidence=(
                id_ocr_result.get("confidence", 0.0) + utility_ocr_result.get("confidence", 0.0)
            )
            / 2.0,
        )
        
        # 6. Calculate initial risk score (simplified)
        kyc.risk_score = self._calculate_risk_score(kyc)
        
        # 7. Mark as submitted
        kyc.submit()
        
        # 8. Save to database
        if existing_kyc:
            kyc.id = existing_kyc.id
            saved_kyc = await self.kyc_repo.update(kyc)
        else:
            saved_kyc = await self.kyc_repo.create(kyc)
        
        logger.info(f"KYC submitted for user {user_id}, verification ID: {saved_kyc.id}")
        
        return saved_kyc
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None
    
    def _calculate_risk_score(self, kyc: KYCVerification) -> int:
        """
        Calculate initial risk score (0-100, lower is better).
        
        Factors:
        - OCR confidence
        - Document expiry
        - Name mismatch between ID and utility bill
        """
        risk = 0
        
        # Low OCR confidence increases risk
        if kyc.overall_confidence < 0.5:
            risk += 30
        elif kyc.overall_confidence < 0.7:
            risk += 15
        
        # Expired document
        if kyc.expiry_date and kyc.expiry_date < datetime.now().date():
            risk += 40
        
        # Name mismatch
        if (
            kyc.full_name
            and kyc.billing_name
            and kyc.full_name.lower() != kyc.billing_name.lower()
        ):
            risk += 20
        
        # Missing critical fields
        if not kyc.full_name or not kyc.document_number:
            risk += 25
        
        return min(risk, 100)
