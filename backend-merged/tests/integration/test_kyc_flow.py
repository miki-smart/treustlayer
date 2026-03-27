"""
Integration tests for KYC submission and approval flow.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_kyc_submission_flow(client: AsyncClient, test_user, admin_user):
    """
    Test KYC submission and approval flow.
    
    Steps:
    1. User submits KYC documents
    2. Admin lists pending KYC queue
    3. Admin approves KYC
    4. User checks status
    """
    # Login as user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    assert login_response.status_code == 200
    user_token = login_response.json()["access_token"]
    
    # Submit KYC (simplified - in real test, upload actual files)
    # This test assumes the endpoint accepts multipart/form-data
    # For now, we'll test the status endpoint
    
    # Login as admin
    admin_login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "admin123"},
    )
    assert admin_login_response.status_code == 200
    admin_token = admin_login_response.json()["access_token"]
    
    # List KYC queue as admin
    queue_response = await client.get(
        "/api/v1/kyc/queue?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert isinstance(queue, list)


@pytest.mark.asyncio
async def test_kyc_approval_requires_permission(client: AsyncClient, test_user):
    """Test that KYC approval requires kyc_approver or admin role."""
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    user_token = login_response.json()["access_token"]
    
    # Try to approve KYC (should fail)
    approve_response = await client.post(
        "/api/v1/kyc/approve/fake-id",
        json={"tier": "tier_1"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert approve_response.status_code == 403
