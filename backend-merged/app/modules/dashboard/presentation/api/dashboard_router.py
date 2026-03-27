"""
Dashboard router — analytics and statistics.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import DBSession, CurrentUserId

router = APIRouter()


class DashboardStats(BaseModel):
    total_users: int
    verified_users: int
    kyc_pending: int
    kyc_approved: int
    total_apps: int
    active_sessions: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get dashboard statistics. Stub implementation."""
    return DashboardStats(
        total_users=0,
        verified_users=0,
        kyc_pending=0,
        kyc_approved=0,
        total_apps=0,
        active_sessions=0,
    )


@router.get("/timeseries")
async def get_timeseries(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get time-series data. Stub implementation."""
    return {"data": []}
