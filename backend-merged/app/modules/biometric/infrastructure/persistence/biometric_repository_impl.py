"""
SQLAlchemy implementation of BiometricRepository.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.biometric.domain.entities.biometric_record import BiometricRecord, BiometricType, BiometricStatus, RiskLevel
from app.modules.biometric.domain.repositories.biometric_repository import BiometricRepository
from app.modules.biometric.infrastructure.persistence.biometric_model import BiometricModel


class SQLAlchemyBiometricRepository(BiometricRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, record: BiometricRecord) -> BiometricRecord:
        model = BiometricModel(
            id=uuid.UUID(record.id),
            user_id=uuid.UUID(record.user_id),
            type=record.type.value,
            status=record.status.value,
            liveness_score=record.liveness_score,
            spoof_probability=record.spoof_probability,
            quality_score=record.quality_score,
            risk_level=record.risk_level.value,
            device_info=record.device_info,
            ip_address=record.ip_address,
            biometric_data_url=record.biometric_data_url,
            biometric_hash=record.biometric_hash,
            verified_at=record.verified_at,
            created_at=record.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_id(self, record_id: str) -> Optional[BiometricRecord]:
        result = await self.session.execute(
            select(BiometricModel).where(BiometricModel.id == uuid.UUID(record_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: str) -> List[BiometricRecord]:
        result = await self.session.execute(
            select(BiometricModel)
            .where(BiometricModel.user_id == uuid.UUID(user_id))
            .order_by(BiometricModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_user_and_type(self, user_id: str, type: BiometricType) -> List[BiometricRecord]:
        result = await self.session.execute(
            select(BiometricModel)
            .where(
                BiometricModel.user_id == uuid.UUID(user_id),
                BiometricModel.type == type.value
            )
            .order_by(BiometricModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_verified_by_user_and_type(self, user_id: str, type: BiometricType) -> Optional[BiometricRecord]:
        result = await self.session.execute(
            select(BiometricModel)
            .where(
                BiometricModel.user_id == uuid.UUID(user_id),
                BiometricModel.type == type.value,
                BiometricModel.status == BiometricStatus.VERIFIED.value
            )
            .order_by(BiometricModel.verified_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 50) -> List[BiometricRecord]:
        result = await self.session.execute(
            select(BiometricModel)
            .order_by(BiometricModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, record: BiometricRecord) -> BiometricRecord:
        result = await self.session.execute(
            select(BiometricModel).where(BiometricModel.id == uuid.UUID(record.id))
        )
        model = result.scalar_one()
        
        model.status = record.status.value
        model.liveness_score = record.liveness_score
        model.spoof_probability = record.spoof_probability
        model.quality_score = record.quality_score
        model.risk_level = record.risk_level.value
        model.device_info = record.device_info
        model.ip_address = record.ip_address
        model.biometric_data_url = record.biometric_data_url
        model.biometric_hash = record.biometric_hash
        model.verified_at = record.verified_at
        
        await self.session.flush()
        return self._to_entity(model)

    async def delete(self, record_id: str) -> None:
        result = await self.session.execute(
            select(BiometricModel).where(BiometricModel.id == uuid.UUID(record_id))
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    def _to_entity(self, model: BiometricModel) -> BiometricRecord:
        return BiometricRecord(
            id=str(model.id),
            user_id=str(model.user_id),
            type=BiometricType(model.type),
            status=BiometricStatus(model.status),
            liveness_score=model.liveness_score,
            spoof_probability=model.spoof_probability,
            quality_score=model.quality_score,
            risk_level=RiskLevel(model.risk_level),
            device_info=model.device_info,
            ip_address=model.ip_address,
            biometric_data_url=model.biometric_data_url,
            biometric_hash=model.biometric_hash,
            verified_at=model.verified_at,
            created_at=model.created_at,
        )
