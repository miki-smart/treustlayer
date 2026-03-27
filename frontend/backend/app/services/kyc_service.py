"""
eKYC service with AI-simulated risk scoring, OCR confidence, and synthetic-identity detection.
"""
import uuid
import random
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.kyc import KYCApplication, KYCStatus
from app.models.user import User
from app.schemas.ocr import OCRExtractedData
from app.utils.audit import write_audit_entry
from app.services import trust_service


def _compute_risk(documents: list[str], ocr_confidence: float, synthetic_prob: float) -> int:
    """Rule-based risk scoring (0–100). Lower is safer."""
    base = 100 - int(ocr_confidence * 60)
    base += int(synthetic_prob * 60)
    base -= len(documents) * 5  # more docs = lower risk
    base = max(0, min(100, base))
    return base


def _simulate_ocr_and_synthetic(documents: list[str]) -> tuple[float, float]:
    """Simulates OCR confidence and synthetic-ID probability from document list."""
    seed = sum(ord(c) for d in documents for c in d)
    ocr = round(0.60 + (seed % 400) / 1000, 3)
    synthetic = round(max(0.0, 1.0 - ocr - 0.3 + (seed % 200) / 2000), 3)
    return min(ocr, 0.99), min(synthetic, 0.99)


async def submit_application(
    db: AsyncSession,
    user: User,
    documents: list[str],
    extracted_data: OCRExtractedData | None = None,
) -> KYCApplication:
    if extracted_data and extracted_data.overall_confidence > 0:
        # Use real Gemini OCR confidence values
        ocr = extracted_data.overall_confidence
        synthetic = round(max(0.0, 1.0 - ocr - 0.25), 3)
    else:
        ocr, synthetic = _simulate_ocr_and_synthetic(documents)

    risk = _compute_risk(documents, ocr, synthetic)

    app = KYCApplication(
        id=uuid.uuid4(),
        user_id=user.id,
        status=KYCStatus.pending,
        risk_score=risk,
        documents_submitted=documents,
        ocr_confidence=ocr,
        synthetic_id_probability=synthetic,
        submitted_at=datetime.now(timezone.utc),
        extracted_data=extracted_data.model_dump() if extracted_data else None,
    )
    db.add(app)
    await write_audit_entry(
        db,
        action="KYC Submitted",
        actor_id=user.id,
        actor_name=user.name,
        target=user.name,
        details=(
            f"KYC application submitted with {len(documents)} document(s). "
            f"Risk score: {risk}. OCR confidence: {ocr:.2f}."
        ),
    )
    return app


async def get_applications(db: AsyncSession, user: User, is_admin: bool) -> list[KYCApplication]:
    query = (
        select(KYCApplication)
        .options(selectinload(KYCApplication.user), selectinload(KYCApplication.reviewer))
        .order_by(KYCApplication.submitted_at.desc())
    )
    if not is_admin:
        query = query.where(KYCApplication.user_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_application_by_id(db: AsyncSession, app_id: uuid.UUID) -> KYCApplication:
    result = await db.execute(
        select(KYCApplication)
        .options(selectinload(KYCApplication.user), selectinload(KYCApplication.reviewer))
        .where(KYCApplication.id == app_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="KYC application not found")
    return app


async def review_application(
    db: AsyncSession,
    app_id: uuid.UUID,
    reviewer: User,
    new_status: KYCStatus,
    notes: str | None,
) -> KYCApplication:
    app = await get_application_by_id(db, app_id)
    app.status = new_status
    app.reviewer_id = reviewer.id
    app.reviewed_at = datetime.now(timezone.utc)
    if notes:
        app.notes = notes
    await write_audit_entry(
        db,
        action=f"KYC {new_status.capitalize()}",
        actor_id=reviewer.id,
        actor_name=reviewer.name,
        target=str(app.user_id),
        details=f"Application {app_id} set to {new_status}. Notes: {notes or '—'}",
    )
    # Re-evaluate trust score when KYC status changes
    applicant_result = await db.execute(
        select(User).where(User.id == app.user_id)
    )
    applicant = applicant_result.scalar_one_or_none()
    if applicant:
        await trust_service.evaluate_trust(db, applicant)
    return app
