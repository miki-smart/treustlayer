import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.lending_engine import (
    OFFER_MATRIX,
    SCORE_RANGE_LABEL_BY_BAND,
    evaluate_decision,
    evaluate_preview,
)

app = FastAPI(title="Lending eligibility API", version="1.0.0")

# Optional: browser → FastAPI during local experiments (Next still uses server-to-server by default).
_cors = os.environ.get("LENDING_API_CORS_ORIGINS", "").strip()
if _cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


def require_api_key(x_lending_api_key: str | None = Header(None, alias="X-Lending-Api-Key")):
    expected = (os.environ.get("LENDING_API_SECRET") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="LENDING_API_SECRET is not configured on the lending API",
        )
    if not x_lending_api_key or x_lending_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Lending-Api-Key")


class BorrowerContext(BaseModel):
    trust_score: float = Field(..., ge=0, le=100)
    risk_flag: bool
    kyc_tier: str = Field(..., description="tier_0 | tier_1 | tier_2")


class PreviewResponse(BaseModel):
    trust_band: int
    eligible: bool
    policy_decision: str
    max_principal_usd: float
    apr_annual_percent: float | None
    max_term_days: int
    offer_label: str
    reason_code: str | None
    trust_score: float
    risk_flag: bool
    kyc_tier: str


class DecisionRequest(BorrowerContext):
    requested_amount: float = Field(..., gt=0)
    loan_term_days: int = Field(..., gt=0)


class DecisionResponse(PreviewResponse):
    decision: str
    approved_amount: float | None
    rejection_reason: str | None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/matrix")
def public_matrix():
    """Trust band → offer row (read-only, no auth). Score ranges map raw trust_score 0–100 → band."""
    bands = {}
    for b in (0, 1, 2):
        row = OFFER_MATRIX[b]
        bands[str(b)] = {
            "trust_score_range": SCORE_RANGE_LABEL_BY_BAND[b],
            "eligible": row["eligible"],
            "max_principal_usd": row["max_principal_usd"],
            "apr_annual_percent": row["apr_annual_percent"],
            "max_term_days": row["max_term_days"],
            "offer_label": row["offer_label"],
        }
    return {"trust_bands": bands}


@app.post("/v1/eligibility/preview", response_model=PreviewResponse)
def post_preview(body: BorrowerContext, _: None = Depends(require_api_key)):
    data = evaluate_preview(
        trust_score=body.trust_score,
        risk_flag=body.risk_flag,
        kyc_tier=body.kyc_tier,
    )
    return PreviewResponse(**data)


@app.post("/v1/eligibility/decision", response_model=DecisionResponse)
def post_decision(body: DecisionRequest, _: None = Depends(require_api_key)):
    data = evaluate_decision(
        trust_score=body.trust_score,
        risk_flag=body.risk_flag,
        kyc_tier=body.kyc_tier,
        requested_amount=body.requested_amount,
        loan_term_days=body.loan_term_days,
    )
    return DecisionResponse(**data)
