"""
Dashboard router � analytics and statistics.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import DBSession, require_admin
from app.modules.dashboard.application.services.analytics_service import AnalyticsService

router = APIRouter()


class DashboardStats(BaseModel):
    total_users: int
    verified_users: int
    kyc_pending: int
    kyc_in_review: int
    kyc_approved: int
    kyc_rejected: int
    total_apps: int
    apps_pending: int
    active_sessions: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: DBSession,
    _: None = Depends(require_admin),
):
    """
    Get dashboard statistics.
    
    Admin only. Returns aggregated metrics.
    """
    analytics = AnalyticsService(session)
    stats = await analytics.get_dashboard_stats()
    
    return DashboardStats(**stats)
