"""
Integration tests for the KYC HTTP API flow.

Flow under test:
  1. POST /kyc/submit/{user_id}          — submit documents
  2. POST /kyc/{kyc_id}/approve          — approve (admin)
  3. GET  /kyc/status/{user_id}          — fetch status
  4. POST /kyc/{kyc_id}/reject           — reject with reason
  5. Resubmit after rejection
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_USER_ID = "00000000-0000-0000-0000-000000000001"

_SUBMIT_PAYLOAD = {
    "document_type": "passport",
    "document_number": "XZ987654",
    "document_url": "https://s3.example.com/doc.jpg",
    "face_image_url": "https://s3.example.com/face.jpg",
}


class TestKYCSubmitApproveFlow:
    async def test_submit_creates_kyc_record(self, integration_client: AsyncClient):
        resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert data["user_id"] == _USER_ID
        assert data["status"] == "submitted"
        assert data["document_type"] == "passport"
        assert data["trust_score"] > 0  # partial score assigned on submit

    async def test_submit_twice_updates_existing(self, integration_client: AsyncClient):
        await integration_client.post(f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD)
        resp2 = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}",
            json={**_SUBMIT_PAYLOAD, "document_number": "XZ000001"},
        )
        assert resp2.status_code == 202, resp2.text
        assert resp2.json()["document_number"] == "XZ000001"

    async def test_approve_sets_tier_and_full_score(self, integration_client: AsyncClient):
        submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        kyc_id = submit_resp.json()["id"]

        approve_resp = await integration_client.post(f"/api/v1/kyc/{kyc_id}/approve")
        assert approve_resp.status_code == 200, approve_resp.text
        data = approve_resp.json()
        assert data["status"] == "approved"
        assert data["tier"] in ("tier_1", "tier_2")
        assert data["trust_score"] >= 50

    async def test_approve_already_approved_returns_409(self, integration_client: AsyncClient):
        submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        kyc_id = submit_resp.json()["id"]
        await integration_client.post(f"/api/v1/kyc/{kyc_id}/approve")

        # Second approve
        resp = await integration_client.post(f"/api/v1/kyc/{kyc_id}/approve")
        assert resp.status_code == 409

    async def test_submit_after_approved_returns_409(self, integration_client: AsyncClient):
        submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        kyc_id = submit_resp.json()["id"]
        await integration_client.post(f"/api/v1/kyc/{kyc_id}/approve")

        # Try re-submit after approval
        resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        assert resp.status_code == 409


class TestKYCRejectFlow:
    async def test_reject_sets_reason(self, integration_client: AsyncClient):
        submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        kyc_id = submit_resp.json()["id"]

        reject_resp = await integration_client.post(
            f"/api/v1/kyc/{kyc_id}/reject",
            json={"reason": "Document appears tampered"},
        )
        assert reject_resp.status_code == 200, reject_resp.text
        data = reject_resp.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Document appears tampered"

    async def test_resubmit_after_rejection_succeeds(self, integration_client: AsyncClient):
        submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD
        )
        kyc_id = submit_resp.json()["id"]
        await integration_client.post(
            f"/api/v1/kyc/{kyc_id}/reject",
            json={"reason": "Unclear photo"},
        )

        # Resubmit should succeed
        resp2 = await integration_client.post(
            f"/api/v1/kyc/submit/{_USER_ID}",
            json={**_SUBMIT_PAYLOAD, "document_url": "https://s3.example.com/clearer.jpg"},
        )
        assert resp2.status_code == 202, resp2.text
        assert resp2.json()["status"] == "submitted"


class TestKYCStatusEndpoint:
    async def test_status_after_submit(self, integration_client: AsyncClient):
        await integration_client.post(f"/api/v1/kyc/submit/{_USER_ID}", json=_SUBMIT_PAYLOAD)

        status_resp = await integration_client.get(f"/api/v1/kyc/status/{_USER_ID}")
        assert status_resp.status_code == 200, status_resp.text
        data = status_resp.json()
        assert data["user_id"] == _USER_ID
        assert data["status"] == "submitted"

    async def test_status_not_found_returns_404(self, integration_client: AsyncClient):
        resp = await integration_client.get("/api/v1/kyc/status/no-such-user-id")
        assert resp.status_code == 404

    async def test_approve_nonexistent_kyc_returns_404(self, integration_client: AsyncClient):
        resp = await integration_client.post("/api/v1/kyc/nonexistent-id/approve")
        assert resp.status_code == 404
