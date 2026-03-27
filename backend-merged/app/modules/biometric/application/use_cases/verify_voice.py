"""
VerifyVoiceUseCase — verify user's voice biometric.
"""
import logging
from typing import Optional

from app.infrastructure.ai.voice_verification_service import voice_verification_service
from app.modules.biometric.domain.entities.biometric_record import BiometricRecord, BiometricType
from app.modules.biometric.domain.repositories.biometric_repository import BiometricRepository

logger = logging.getLogger(__name__)


class VerifyVoiceUseCase:
    def __init__(self, biometric_repo: BiometricRepository):
        self.biometric_repo = biometric_repo

    async def execute(
        self,
        user_id: str,
        audio_bytes: bytes,
        device_info: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> BiometricRecord:
        """
        Verify voice biometric.
        
        Steps:
        1. Verify voice sample (liveness, spoof detection)
        2. Create biometric record
        3. Determine verification status
        """
        liveness_score, spoof_probability, quality_score = await voice_verification_service.verify_voice(
            audio_bytes
        )
        
        logger.info(
            f"Voice verification for user {user_id}: "
            f"liveness={liveness_score:.2f}, spoof={spoof_probability:.2f}, quality={quality_score:.2f}"
        )
        
        record = BiometricRecord(
            user_id=user_id,
            type=BiometricType.VOICE,
            liveness_score=liveness_score,
            spoof_probability=spoof_probability,
            quality_score=quality_score,
            device_info=device_info,
            ip_address=ip_address,
        )
        
        record.risk_level = record.calculate_risk_level()
        
        if liveness_score >= 0.7 and spoof_probability <= 0.3 and quality_score >= 0.5:
            record.verify()
            logger.info(f"Voice verification PASSED for user {user_id}")
        else:
            record.fail()
            logger.warning(f"Voice verification FAILED for user {user_id}")
        
        saved_record = await self.biometric_repo.create(record)
        
        return saved_record
