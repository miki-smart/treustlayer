"""
Trust score → discrete band 0 | 1 | 2, then matrix-driven eligibility and loan offer.
Raw trust_score is assumed on a 0–100 scale from TrustIdLayer introspection.
"""

from __future__ import annotations

from typing import Any, Literal

TrustBand = Literal[0, 1, 2]

# Band thresholds on 0–100 trust_score (inclusive upper bound for lower bands)
BAND1_MAX_SCORE = 33  # [0, BAND1_MAX_SCORE] → band 0
BAND2_MAX_SCORE = 66  # (BAND1_MAX_SCORE, BAND2_MAX_SCORE] → band 1, else band 2

SCORE_RANGE_LABEL_BY_BAND: dict[TrustBand, str] = {
    0: f"0–{BAND1_MAX_SCORE}",
    1: f"{BAND1_MAX_SCORE + 1}–{BAND2_MAX_SCORE}",
    2: f"{BAND2_MAX_SCORE + 1}–100",
}

# Matrix keyed by trust band (0 = lowest trust tier for lending)
OFFER_MATRIX: dict[TrustBand, dict[str, Any]] = {
    0: {
        "eligible": False,
        "max_principal_usd": 0.0,
        "apr_annual_percent": None,
        "max_term_days": 0,
        "offer_label": "not_eligible",
    },
    1: {
        "eligible": True,
        "max_principal_usd": 3_500.0,
        "apr_annual_percent": 15.9,
        "max_term_days": 180,
        "offer_label": "standard",
    },
    2: {
        "eligible": True,
        "max_principal_usd": 15_000.0,
        "apr_annual_percent": 10.5,
        "max_term_days": 365,
        "offer_label": "preferred",
    },
}


def trust_score_to_band(trust_score: float) -> TrustBand:
    s = float(trust_score)
    if s <= BAND1_MAX_SCORE:
        return 0
    if s <= BAND2_MAX_SCORE:
        return 1
    return 2


def evaluate_preview(
    *,
    trust_score: float,
    risk_flag: bool,
    kyc_tier: str,
) -> dict[str, Any]:
    if risk_flag:
        band = trust_score_to_band(trust_score)
        return _rejection_payload(
            band=band,
            reason_code="risk_flag_high_risk",
            trust_score=trust_score,
            risk_flag=risk_flag,
            kyc_tier=kyc_tier,
        )
    if kyc_tier == "tier_0":
        band = trust_score_to_band(trust_score)
        return _rejection_payload(
            band=band,
            reason_code="kyc_tier_insufficient",
            trust_score=trust_score,
            risk_flag=risk_flag,
            kyc_tier=kyc_tier,
        )

    band = trust_score_to_band(trust_score)
    row = OFFER_MATRIX[band]
    if not row["eligible"]:
        return _rejection_payload(
            band=band,
            reason_code="trust_band_ineligible",
            trust_score=trust_score,
            risk_flag=risk_flag,
            kyc_tier=kyc_tier,
        )

    return {
        "trust_band": band,
        "eligible": True,
        "policy_decision": "approved",
        "max_principal_usd": row["max_principal_usd"],
        "apr_annual_percent": row["apr_annual_percent"],
        "max_term_days": row["max_term_days"],
        "offer_label": row["offer_label"],
        "reason_code": None,
        "trust_score": trust_score,
        "risk_flag": risk_flag,
        "kyc_tier": kyc_tier,
    }


def evaluate_decision(
    *,
    trust_score: float,
    risk_flag: bool,
    kyc_tier: str,
    requested_amount: float,
    loan_term_days: int,
) -> dict[str, Any]:
    base = evaluate_preview(
        trust_score=trust_score, risk_flag=risk_flag, kyc_tier=kyc_tier
    )
    if not base.get("eligible"):
        return {
            **base,
            "decision": "rejected",
            "approved_amount": None,
            "rejection_reason": base.get("reason_code"),
        }

    max_p = float(base["max_principal_usd"])
    max_term = int(base["max_term_days"])

    if requested_amount > max_p:
        return {
            **base,
            "eligible": False,
            "policy_decision": "rejected",
            "decision": "rejected",
            "approved_amount": None,
            "rejection_reason": "amount_exceeds_max",
        }
    if loan_term_days > max_term:
        return {
            **base,
            "eligible": False,
            "policy_decision": "rejected",
            "decision": "rejected",
            "approved_amount": None,
            "rejection_reason": "term_exceeds_max",
        }

    return {
        **base,
        "decision": "approved",
        "approved_amount": requested_amount,
        "rejection_reason": None,
    }


def _rejection_payload(
    *,
    band: TrustBand,
    reason_code: str,
    trust_score: float,
    risk_flag: bool,
    kyc_tier: str,
) -> dict[str, Any]:
    row = OFFER_MATRIX[band]
    return {
        "trust_band": band,
        "eligible": False,
        "policy_decision": "rejected",
        "max_principal_usd": row["max_principal_usd"],
        "apr_annual_percent": row["apr_annual_percent"],
        "max_term_days": row["max_term_days"],
        "offer_label": row["offer_label"],
        "reason_code": reason_code,
        "trust_score": trust_score,
        "risk_flag": risk_flag,
        "kyc_tier": kyc_tier,
    }
