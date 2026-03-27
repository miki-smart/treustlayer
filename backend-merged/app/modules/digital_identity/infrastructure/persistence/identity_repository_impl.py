"""
SQLAlchemy implementation of DigitalIdentityRepository.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.digital_identity.domain.entities.digital_identity import (
    DigitalIdentity,
    IdentityAttribute,
    IdentityCredential,
    IdentityStatus,
)
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository
from app.modules.digital_identity.infrastructure.persistence.identity_model import (
    DigitalIdentityModel,
    IdentityAttributeModel,
    IdentityCredentialModel,
)


class SQLAlchemyDigitalIdentityRepository(DigitalIdentityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, identity: DigitalIdentity) -> DigitalIdentity:
        model = DigitalIdentityModel(
            id=uuid.UUID(identity.id),
            user_id=uuid.UUID(identity.user_id),
            unique_id=identity.unique_id,
            status=identity.status.value,
            created_at=identity.created_at,
            last_verified=identity.last_verified,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_id(self, identity_id: str) -> Optional[DigitalIdentity]:
        result = await self.session.execute(
            select(DigitalIdentityModel).where(DigitalIdentityModel.id == uuid.UUID(identity_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, user_id: str) -> Optional[DigitalIdentity]:
        result = await self.session.execute(
            select(DigitalIdentityModel).where(DigitalIdentityModel.user_id == uuid.UUID(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_unique_id(self, unique_id: str) -> Optional[DigitalIdentity]:
        result = await self.session.execute(
            select(DigitalIdentityModel).where(DigitalIdentityModel.unique_id == unique_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, identity: DigitalIdentity) -> DigitalIdentity:
        result = await self.session.execute(
            select(DigitalIdentityModel).where(DigitalIdentityModel.id == uuid.UUID(identity.id))
        )
        model = result.scalar_one()
        
        model.status = identity.status.value
        model.last_verified = identity.last_verified
        
        await self.session.flush()
        return self._to_entity(model)

    async def add_attribute(self, attr: IdentityAttribute) -> IdentityAttribute:
        model = IdentityAttributeModel(
            id=uuid.UUID(attr.id),
            identity_id=uuid.UUID(attr.identity_id),
            key=attr.key,
            value=attr.value,
            is_shared=attr.is_shared,
            created_at=attr.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._attr_to_entity(model)

    async def get_attributes(self, identity_id: str) -> List[IdentityAttribute]:
        result = await self.session.execute(
            select(IdentityAttributeModel)
            .where(IdentityAttributeModel.identity_id == uuid.UUID(identity_id))
            .order_by(IdentityAttributeModel.key)
        )
        return [self._attr_to_entity(m) for m in result.scalars().all()]

    async def get_attribute(self, identity_id: str, key: str) -> Optional[IdentityAttribute]:
        result = await self.session.execute(
            select(IdentityAttributeModel).where(
                and_(
                    IdentityAttributeModel.identity_id == uuid.UUID(identity_id),
                    IdentityAttributeModel.key == key
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._attr_to_entity(model) if model else None

    async def update_attribute(self, attr: IdentityAttribute) -> IdentityAttribute:
        result = await self.session.execute(
            select(IdentityAttributeModel).where(IdentityAttributeModel.id == uuid.UUID(attr.id))
        )
        model = result.scalar_one()
        
        model.value = attr.value
        model.is_shared = attr.is_shared
        
        await self.session.flush()
        return self._attr_to_entity(model)

    async def delete_attribute(self, identity_id: str, key: str) -> None:
        result = await self.session.execute(
            select(IdentityAttributeModel).where(
                and_(
                    IdentityAttributeModel.identity_id == uuid.UUID(identity_id),
                    IdentityAttributeModel.key == key
                )
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def issue_credential(self, cred: IdentityCredential) -> IdentityCredential:
        model = IdentityCredentialModel(
            id=uuid.UUID(cred.id),
            identity_id=uuid.UUID(cred.identity_id),
            type=cred.type,
            issuer=cred.issuer,
            credential_data=cred.credential_data,
            expires_at=cred.expires_at,
            status=cred.status,
            issued_at=cred.issued_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._cred_to_entity(model)

    async def get_credentials(self, identity_id: str) -> List[IdentityCredential]:
        result = await self.session.execute(
            select(IdentityCredentialModel)
            .where(IdentityCredentialModel.identity_id == uuid.UUID(identity_id))
            .order_by(IdentityCredentialModel.issued_at.desc())
        )
        return [self._cred_to_entity(m) for m in result.scalars().all()]

    async def get_credential(self, credential_id: str) -> Optional[IdentityCredential]:
        result = await self.session.execute(
            select(IdentityCredentialModel).where(IdentityCredentialModel.id == uuid.UUID(credential_id))
        )
        model = result.scalar_one_or_none()
        return self._cred_to_entity(model) if model else None

    async def update_credential(self, cred: IdentityCredential) -> IdentityCredential:
        result = await self.session.execute(
            select(IdentityCredentialModel).where(IdentityCredentialModel.id == uuid.UUID(cred.id))
        )
        model = result.scalar_one()
        
        model.status = cred.status
        
        await self.session.flush()
        return self._cred_to_entity(model)

    def _to_entity(self, model: DigitalIdentityModel) -> DigitalIdentity:
        return DigitalIdentity(
            id=str(model.id),
            user_id=str(model.user_id),
            unique_id=model.unique_id,
            status=IdentityStatus(model.status),
            created_at=model.created_at,
            last_verified=model.last_verified,
        )

    def _attr_to_entity(self, model: IdentityAttributeModel) -> IdentityAttribute:
        return IdentityAttribute(
            id=str(model.id),
            identity_id=str(model.identity_id),
            key=model.key,
            value=model.value,
            is_shared=model.is_shared,
            created_at=model.created_at,
        )

    def _cred_to_entity(self, model: IdentityCredentialModel) -> IdentityCredential:
        return IdentityCredential(
            id=str(model.id),
            identity_id=str(model.identity_id),
            type=model.type,
            issuer=model.issuer,
            credential_data=model.credential_data,
            expires_at=model.expires_at,
            status=model.status,
            issued_at=model.issued_at,
        )
