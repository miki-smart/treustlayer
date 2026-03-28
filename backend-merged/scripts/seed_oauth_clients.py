"""
Upsert pre-provisioned OAuth2 clients (e.g. from appkeys) into app_registry.apps.

Run from backend-merged root after migrations and seed_demo_users:

  set LENDING_OAUTH_CLIENT_SECRET=...
  set PAYMENT_OAUTH_CLIENT_SECRET=...
  python scripts/seed_oauth_clients.py

On Unix:
  export LENDING_OAUTH_CLIENT_SECRET=...
  export PAYMENT_OAUTH_CLIENT_SECRET=...
  python scripts/seed_oauth_clients.py

Uses the same hashing as RegisterAppUseCase (hash_secret). Does not print secrets.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Scopes aligned with AuthorizeUseCase + product needs
DEFAULT_SCOPES = [
    "openid",
    "profile",
    "email",
    "phone",
    "kyc_status",
    "trust_score",
]

LENDING = {
    "name": "Lending App",
    "client_id": "app_e03fc733d51d48ec",
    "env_secret": "LENDING_OAUTH_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:3000/auth/callback"],
    "description": "Lending desk integrated with TrustLayer ID",
    "category": "finance",
}

PAYMENT = {
    "name": "Payment App",
    "client_id": "app_7b0b6bb71afb49e4",
    "env_secret": "PAYMENT_OAUTH_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:8080/auth/callback"],
    "description": "Payments with trust-based limits",
    "category": "finance",
}


async def _owner_id(session) -> str:
    from sqlalchemy import select
    from app.modules.identity.infrastructure.persistence.user_model import UserModel

    result = await session.execute(
        select(UserModel).where(UserModel.email == "dev@example.com")
    )
    row = result.scalar_one_or_none()
    if row:
        return str(row.id)
    result = await session.execute(
        select(UserModel).where(UserModel.email == "admin@fininfra.io")
    )
    row = result.scalar_one_or_none()
    if row:
        return str(row.id)
    raise RuntimeError(
        "No dev@example.com or admin@fininfra.io user found. Run scripts/seed_demo_users.py first."
    )


async def _upsert_app(
    session,
    *,
    owner_id: str,
    spec: dict,
    client_secret_plain: str,
) -> None:
    from app.core.security import generate_secure_token, hash_secret
    from app.modules.app_registry.infrastructure.persistence.app_model import AppModel
    from sqlalchemy import select

    client_secret_hash = hash_secret(client_secret_plain)
    api_key = generate_secure_token(32)
    api_key_hash = hash_secret(api_key)

    result = await session.execute(
        select(AppModel).where(AppModel.client_id == spec["client_id"])
    )
    model = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if model:
        model.client_secret_hash = client_secret_hash
        model.api_key_hash = api_key_hash
        model.name = spec["name"]
        model.owner_id = uuid.UUID(owner_id)
        model.allowed_scopes = DEFAULT_SCOPES
        model.redirect_uris = spec["redirect_uris"]
        model.description = spec["description"]
        model.category = spec["category"]
        model.is_active = True
        model.is_approved = True
        model.is_public = True
        model.updated_at = now
        print(f"Updated app registry row: {spec['client_id']}")
    else:
        m = AppModel(
            id=uuid.uuid4(),
            name=spec["name"],
            owner_id=uuid.UUID(owner_id),
            client_id=spec["client_id"],
            client_secret_hash=client_secret_hash,
            api_key_hash=api_key_hash,
            allowed_scopes=DEFAULT_SCOPES,
            redirect_uris=spec["redirect_uris"],
            description=spec["description"],
            logo_url=None,
            category=spec["category"],
            is_active=True,
            is_approved=True,
            is_public=True,
            created_at=now,
            updated_at=now,
        )
        session.add(m)
        print(f"Inserted app registry row: {spec['client_id']}")


async def main() -> None:
    lend_sec = (os.environ.get(LENDING["env_secret"]) or "").strip()
    pay_sec = (os.environ.get(PAYMENT["env_secret"]) or "").strip()
    if not lend_sec or not pay_sec:
        print(
            f"Set {LENDING['env_secret']} and {PAYMENT['env_secret']} "
            "to the plaintext client secrets from your appkeys file.",
            file=sys.stderr,
        )
        sys.exit(1)

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        owner_id = await _owner_id(session)
        await _upsert_app(session, owner_id=owner_id, spec=LENDING, client_secret_plain=lend_sec)
        await _upsert_app(session, owner_id=owner_id, spec=PAYMENT, client_secret_plain=pay_sec)
        await session.commit()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
