"""
Alembic env.py — async-compatible with SQLAlchemy 2.0.
Imports all ORM models so Alembic can autogenerate migrations.
"""
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.infrastructure.db.base import Base

# ── Import ALL models so metadata is populated ────────────────────────────────
# flake8: noqa
from app.modules.identity.infrastructure.persistence.user_model import UserModel
from app.modules.app_registry.infrastructure.persistence.app_model import RegisteredAppModel
from app.modules.auth.infrastructure.persistence.auth_code_model import AuthorizationCodeModel
from app.modules.kyc.infrastructure.persistence.kyc_model import KYCVerificationModel
from app.modules.consent.infrastructure.persistence.consent_model import ConsentModel
from app.modules.session.infrastructure.persistence.refresh_token_model import RefreshTokenModel
from app.modules.webhook.infrastructure.persistence.webhook_model import (
    WebhookSubscriptionModel,
    WebhookDeliveryModel,
)

# Alembic Config object
config = context.config

# Set up loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return settings.DATABASE_URL


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        compare_type=True,
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(get_url())
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()
