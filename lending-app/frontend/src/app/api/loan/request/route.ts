import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE } from "@/lib/cookies";
import { runLoanDecision, type LoanRequestBody } from "@/lib/loan-service";

function auditLog(entry: Record<string, unknown>) {
  console.info(JSON.stringify({ type: "loan_decision", ...entry }));
}

export async function POST(req: Request) {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  let body: Partial<LoanRequestBody>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const requested_amount = Number(body.requested_amount);
  const currency = typeof body.currency === "string" ? body.currency : "USD";
  const loan_term_days = Number(body.loan_term_days);

  if (!Number.isFinite(requested_amount) || requested_amount <= 0) {
    return NextResponse.json({ error: "invalid_requested_amount" }, { status: 400 });
  }
  if (!Number.isFinite(loan_term_days) || loan_term_days <= 0) {
    return NextResponse.json({ error: "invalid_loan_term_days" }, { status: 400 });
  }

  const decision = await runLoanDecision(token, {
    requested_amount,
    currency,
    loan_term_days,
  });

  auditLog({
    user_id: decision.user_sub ?? null,
    trust_score: decision.trust_score_used,
    kyc_tier: decision.kyc_tier_used,
    risk_flag: decision.risk_flag_used,
    trust_band: decision.offer?.trust_band ?? null,
    decision: decision.decision,
    reason_code:
      decision.decision === "approved"
        ? "approved"
        : "reason" in decision
          ? decision.reason
          : "unknown",
    requested_amount,
    timestamp: decision.decision_timestamp,
    lending_engine: decision.offer ? "fastapi" : "next_policy",
  });

  const offerFields = decision.offer
    ? {
        trust_band: decision.offer.trust_band,
        apr_annual_percent: decision.offer.apr_annual_percent,
        max_term_days: decision.offer.max_term_days,
        offer_label: decision.offer.offer_label,
        lending_engine: "fastapi" as const,
      }
    : { lending_engine: "next_policy" as const };

  if (decision.decision === "approved") {
    return NextResponse.json({
      decision: "approved",
      approved_amount: decision.approved_amount,
      kyc_tier_used: decision.kyc_tier_used,
      trust_score_used: decision.trust_score_used,
      risk_flag_used: decision.risk_flag_used,
      decision_timestamp: decision.decision_timestamp,
      loan_reference: decision.loan_reference,
      ...offerFields,
    });
  }

  if (decision.decision === "manual_review") {
    return NextResponse.json({
      decision: "manual_review",
      reason: decision.reason,
      kyc_tier_used: decision.kyc_tier_used,
      trust_score_used: decision.trust_score_used,
      risk_flag_used: decision.risk_flag_used,
      decision_timestamp: decision.decision_timestamp,
      ...offerFields,
    });
  }

  return NextResponse.json({
    decision: "rejected",
    reason: decision.reason,
    kyc_tier_used: decision.kyc_tier_used,
    trust_score_used: decision.trust_score_used,
    risk_flag_used: decision.risk_flag_used,
    decision_timestamp: decision.decision_timestamp,
    ...offerFields,
  });
}
