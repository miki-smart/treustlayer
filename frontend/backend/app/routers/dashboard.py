from fastapi import APIRouter
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, timedelta

from app.dependencies import CurrentUser, DB
from app.schemas.dashboard import DashboardStats, MonthlyDataPoint
from app.models.user import User
from app.models.kyc import KYCApplication, KYCStatus
from app.models.identity import DigitalIdentity, IdentityStatus
from app.models.card import FinCard, CardTransaction, TransactionStatus
from app.models.sso import SSOSession, SSOSessionStatus
from app.models.biometric import BiometricRecord

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(current_user: CurrentUser, db: DB):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_identities = (await db.execute(
        select(func.count()).select_from(DigitalIdentity).where(DigitalIdentity.status == IdentityStatus.active)
    )).scalar_one()
    kyc_completed = (await db.execute(
        select(func.count()).select_from(KYCApplication).where(KYCApplication.status == KYCStatus.approved)
    )).scalar_one()
    card_issued = (await db.execute(select(func.count()).select_from(FinCard))).scalar_one()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    transactions_today = (await db.execute(
        select(func.count()).select_from(CardTransaction).where(CardTransaction.timestamp >= today_start)
    )).scalar_one()
    fraud_blocked = (await db.execute(
        select(func.count()).select_from(CardTransaction).where(CardTransaction.status == TransactionStatus.flagged)
    )).scalar_one()
    sso_logins = (await db.execute(select(func.count()).select_from(SSOSession))).scalar_one()
    biometric_verifications = (await db.execute(select(func.count()).select_from(BiometricRecord))).scalar_one()

    return DashboardStats(
        totalUsers=total_users,
        activeIdentities=active_identities,
        kycCompleted=kyc_completed,
        cardIssued=card_issued,
        transactionsToday=transactions_today,
        fraudBlocked=fraud_blocked,
        ssoLogins=sso_logins,
        biometricVerifications=biometric_verifications,
    )


@router.get("/monthly", response_model=list[MonthlyDataPoint])
async def get_monthly(current_user: CurrentUser, db: DB):
    """Returns last 6 months of aggregated data."""
    months = []
    now = datetime.now(timezone.utc)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i in range(5, -1, -1):
        # approximate months as 30-day buckets
        end = now - timedelta(days=30 * i)
        start = end - timedelta(days=30)
        month_label = month_names[(end.month - 1) % 12]

        users = (await db.execute(
            select(func.count()).select_from(User).where(User.created_at <= end)
        )).scalar_one()
        kyc = (await db.execute(
            select(func.count()).select_from(KYCApplication).where(
                and_(KYCApplication.submitted_at >= start, KYCApplication.submitted_at < end)
            )
        )).scalar_one()
        transactions = (await db.execute(
            select(func.count()).select_from(CardTransaction).where(
                and_(CardTransaction.timestamp >= start, CardTransaction.timestamp < end)
            )
        )).scalar_one()

        months.append(MonthlyDataPoint(month=month_label, users=users, kyc=kyc, transactions=transactions))

    return months
