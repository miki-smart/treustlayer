import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE } from "@/lib/cookies";
import { runEligibilityPreview } from "@/lib/loan-service";

export async function GET() {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const preview = await runEligibilityPreview(token);
  if (!preview.ok) {
    return NextResponse.json(
      { error: preview.reason, eligible: false },
      { status: preview.reason === "inactive" ? 401 : 503 },
    );
  }

  const body: Record<string, unknown> = {
    eligible: preview.policy.decision === "approved",
    kyc_tier: preview.kyc_tier,
    trust_score: preview.trust_score,
    risk_flag: preview.risk_flag,
    decision: preview.policy.decision,
    max_lendable_usd: preview.policy.maxLendableUsd,
    reason_code: preview.policy.reasonCode,
    lending_engine: preview.offer ? "fastapi" : "next_policy",
  };

  if (preview.offer) {
    body.trust_band = preview.offer.trust_band;
    body.apr_annual_percent = preview.offer.apr_annual_percent;
    body.max_term_days = preview.offer.max_term_days;
    body.offer_label = preview.offer.offer_label;
  }

  return NextResponse.json(body);
}
