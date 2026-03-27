"""
VerifyFaceUseCase — verify user's face biometric.
"""
import logging
from typing import Optional

from app.core.exceptions import DomainError
from app.infrastructure.ai.face_verification_service import face_verification_service
from app.modules.biometric.domain.entities.biometric_record import BiometricRecord, BiometricType, BiometricStatus
from app.modules.biometric.domain.repositories.biometric_repository import BiometricRepository

logger = logging.getLogger(__name__)


class VerifyFaceUseCase:
    def __init__(self, biometric_repo: BiometricRepository):
        self.biometric_repo = biometric_repo

    async def execute(
        self,
        user_id: str,
        face_image_bytes: bytes,
        id_photo_bytes: Optional[bytes] = None,
        device_info: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> BiometricRecord:
        """
        Verify face biometric.
        
        Steps:
        1. Verify face image (liveness, spoof detection)
        2. If ID photo provided, match faces
        3. Create biometric record
        4. Determine verification status
        """
        liveness_score, spoof_probability, quality_score = await face_verification_service.verify_face(
            face_image_bytes, id_photo_bytes
        )
        
        logger.info(
            f"Face verification for user {user_id}: "
            f"liveness={liveness_score:.2f}, spoof={spoof_probability:.2f}, quality={quality_score:.2f}"
        )
        
        record = BiometricRecord(
            user_id=user_id,
            type=BiometricType.FACE,
            liveness_score=liveness_score,
            spoof_probability=spoof_probability,
            quality_score=quality_score,
            device_info=device_info,
            ip_address=ip_address,
        )
        
        record.risk_level = record.calculate_risk_level()
        
        if liveness_score >= 0.7 and spoof_probability <= 0.3 and quality_score >= 0.6:
            record.verify()
            logger.info(f"Face verification PASSED for user {user_id}")
        else:
            record.fail()
            logger.warning(f"Face verification FAILED for user {user_id}")
        
        saved_record = await self.biometric_repo.create(record)
        
        return saved_record
