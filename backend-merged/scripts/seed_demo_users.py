"""
Create or refresh demo users (passwords + roles) for local / hackathon use.

Run from backend-merged root (or /app in Docker):

  python scripts/seed_demo_users.py

Requires DATABASE_URL (e.g. from .env) and applied migrations.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass(frozen=True)
class DemoUser:
    email: str
    username: str
    password: str
    role: str  # UserRole value
    full_name: str | None


DEMO_USERS: tuple[DemoUser, ...] = (
    DemoUser("admin@fininfra.io", "admin", "admin123", "admin", "Admin User"),
    DemoUser("abebe@example.com", "abebe", "user123", "user", "Abebe Kebede"),
    # Same role as abebe; use for demos where no KYC/trust history should exist (new identity only).
    DemoUser("fresh@example.com", "fresh_demo", "fresh123", "user", "Fresh Demo User"),
    DemoUser("kyc@example.com", "kyc_reviewer", "kyc123", "kyc_approver", "KYC Verifier"),
    DemoUser("dev@example.com", "app_dev", "dev123", "app_owner", "App Owner"),
)


async def main() -> None:
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.modules.identity.domain.entities.user import User, UserRole
    from app.modules.identity.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyUserRepository(session)
        for d in DEMO_USERS:
            role = UserRole(d.role)
            existing = await repo.get_by_email(d.email)
            h = hash_password(d.password)
            if existing:
                existing.hashed_password = h
                existing.role = role
                existing.is_email_verified = True
                existing.is_active = True
                existing.full_name = d.full_name
                existing.updated_at = datetime.now(timezone.utc)
                await repo.update(existing)
                print(f"Updated: {d.email} ({d.role})")
            else:
                user = User(
                    email=d.email,
                    username=d.username,
                    hashed_password=h,
                    full_name=d.full_name,
                    role=role,
                    is_active=True,
                    is_email_verified=True,
                )
                await repo.create(user)
                print(f"Created: {d.email} ({d.role})")
        await session.commit()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
