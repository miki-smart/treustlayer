"""
ConsentService — cross-module public interface.
Auth module calls this to check/grant consent before issuing auth codes.
"""
from typing import List, Optional

from app.core.events import event_bus
from app.modules.consent.domain.entities.consent import Consent
from app.modules.consent.domain.events.consent_events import ConsentGrantedEvent, ConsentRevokedEvent
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository


class ConsentService:
    def __init__(self, consent_repository: ConsentRepository) -> None:
        self._repo = consent_repository

    async def has_consent(
        self, user_id: str, client_id: str, scopes: List[str]
    ) -> bool:
        consent = await self._repo.get_active(user_id, client_id)
        return bool(consent and consent.covers_scopes(scopes))

    async def grant_consent(
        self, user_id: str, client_id: str, scopes: List[str]
    ) -> Consent:
        existing = await self._repo.get_active(user_id, client_id)
        if existing:
            # Merge new scopes into existing consent
            merged = list(set(existing.scopes) | set(scopes))
            existing.scopes = merged
            consent = await self._repo.update(existing)
        else:
            consent = Consent(user_id=user_id, client_id=client_id, scopes=scopes)
            consent = await self._repo.create(consent)

        await event_bus.publish(
            ConsentGrantedEvent(
                user_id=user_id,
                client_id=client_id,
                scopes=" ".join(scopes),
            )
        )
        return consent

    async def revoke_consent(self, user_id: str, client_id: str) -> None:
        consent = await self._repo.get_active(user_id, client_id)
        if consent:
            await self._repo.revoke(consent.id)
            await event_bus.publish(
                ConsentRevokedEvent(
                    user_id=user_id,
                    client_id=client_id,
                    consent_id=consent.id,
                )
            )

    async def list_consents(self, user_id: str) -> List[Consent]:
        return await self._repo.get_all_for_user(user_id)
