"""
AnalyticsService — dashboard statistics and analytics.
"""
import logging
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.infrastructure.persistence.user_model import UserModel
from app.modules.kyc.infrastructure.persistence.kyc_model import KYCModel
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus
from app.modules.app_registry.infrastructure.persistence.app_model import AppModel
from app.modules.auth.infrastructure.persistence.auth_model import RefreshTokenModel

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics service for dashboard statistics.
    
    Provides aggregated metrics for admin dashboard.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Returns:
            Dict with various statistics
        """
        # Total users
        total_users_result = await self.session.execute(
            select(func.count(UserModel.id))
        )
        total_users = total_users_result.scalar() or 0
        
        # Verified users (email verified)
        verified_users_result = await self.session.execute(
            select(func.count(UserModel.id)).where(UserModel.is_email_verified == True)
        )
        verified_users = verified_users_result.scalar() or 0
        
        # KYC pending
        kyc_pending_result = await self.session.execute(
            select(func.count(KYCModel.id)).where(
                KYCModel.status == KYCStatus.PENDING.value
            )
        )
        kyc_pending = kyc_pending_result.scalar() or 0
        
        # KYC approved
        kyc_approved_result = await self.session.execute(
            select(func.count(KYCModel.id)).where(
                KYCModel.status == KYCStatus.APPROVED.value
            )
        )
        kyc_approved = kyc_approved_result.scalar() or 0
        
        # Total apps
        total_apps_result = await self.session.execute(
            select(func.count(AppModel.id))
        )
        total_apps = total_apps_result.scalar() or 0
        
        # Active sessions (non-revoked refresh tokens)
        active_sessions_result = await self.session.execute(
            select(func.count(RefreshTokenModel.id)).where(
                RefreshTokenModel.is_revoked == False
            )
        )
        active_sessions = active_sessions_result.scalar() or 0
        
        # Apps pending approval
        apps_pending_result = await self.session.execute(
            select(func.count(AppModel.id)).where(
                AppModel.is_approved == False
            )
        )
        apps_pending = apps_pending_result.scalar() or 0
        
        # KYC in review
        kyc_in_review_result = await self.session.execute(
            select(func.count(KYCModel.id)).where(
                KYCModel.status == KYCStatus.IN_REVIEW.value
            )
        )
        kyc_in_review = kyc_in_review_result.scalar() or 0
        
        # KYC rejected
        kyc_rejected_result = await self.session.execute(
            select(func.count(KYCModel.id)).where(
                KYCModel.status == KYCStatus.REJECTED.value
            )
        )
        kyc_rejected = kyc_rejected_result.scalar() or 0
        
        logger.info("Dashboard stats retrieved")
        
        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "kyc_pending": kyc_pending,
            "kyc_in_review": kyc_in_review,
            "kyc_approved": kyc_approved,
            "kyc_rejected": kyc_rejected,
            "total_apps": total_apps,
            "apps_pending": apps_pending,
            "active_sessions": active_sessions,
        }
