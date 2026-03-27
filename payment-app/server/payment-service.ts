import { evaluatePolicy } from "../shared/policy";
import type { KycTier } from "../shared/types";
import { introspectToken, validateIntrospectionData } from "./introspect";
import { isTokenExpired } from "./jwt";
import { isUserBlocked } from "./user-blocks";
export type TransactionDecision = "allowed" | "step_up_required" | "rejected";

export interface AuthorizeBody {
  user_id: string;
  amount: number;
  currency: string;
  recipient_id: string;
  transaction_type: string;
  idempotency_key: string;
  user_access_token: string;
}

export interface AuthorizeResponse {
  decision: TransactionDecision;
  transaction_id?: string;
  amount: number;
  currency: string;
  kyc_tier_used: KycTier;
  trust_score_used: number;
  risk_flag_used: boolean;
  reason?: string;
  step_up_method?: string;
  transaction_ref?: string;
  decision_timestamp: string;
}

const idempotency = new Map<string, AuthorizeResponse>();
const dailySpend = new Map<string, { day: string; total: number }>();
let txnCounter = 456;

function utcDay(): string {
  return new Date().toISOString().slice(0, 10);
}

function dailyKey(userId: string): string {
  return `${userId}:${utcDay()}`;
}

function getDailyTotal(userId: string): number {
  const k = dailyKey(userId);
  const row = dailySpend.get(k);
  const day = utcDay();
  if (!row || row.day !== day) {
    dailySpend.set(k, { day, total: 0 });
    return 0;
  }
  return row.total;
}

function addDailySpend(userId: string, amount: number): void {
  const k = dailyKey(userId);
  const day = utcDay();
  const row = dailySpend.get(k);
  if (!row || row.day !== day) {
    dailySpend.set(k, { day, total: amount });
  } else {
    row.total += amount;
  }
}

function nextTxnId(): string {
  txnCounter += 1;
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return `TXN-${d}-${String(txnCounter).padStart(5, "0")}`;
}

export async function authorizePayment(body: AuthorizeBody): Promise<AuthorizeResponse> {
  const ts = new Date().toISOString();
  const cached = idempotency.get(body.idempotency_key);
  if (cached) {
    return { ...cached };
  }

  const block = isUserBlocked(body.user_id);
  if (block.blocked) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: "tier_0",
      trust_score_used: 0,
      risk_flag_used: true,
      reason: block.reason ?? "user_blocked",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  if (!body.user_access_token?.trim()) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: "tier_0",
      trust_score_used: 0,
      risk_flag_used: false,
      reason: "missing_token",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  if (!body.user_access_token.startsWith("demo:") && isTokenExpired(body.user_access_token)) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: "tier_0",
      trust_score_used: 0,
      risk_flag_used: false,
      reason: "token_expired",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  const intro = await introspectToken(body.user_access_token, body.user_id);
  if (!intro.ok) {
    const reasonMap: Record<string, string> = {
      circuit_open: "introspection_unavailable",
      introspection_unavailable: "introspection_unavailable",
      invalid_demo_token: "introspection_unavailable",
    };
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: "tier_0",
      trust_score_used: 0,
      risk_flag_used: false,
      reason: reasonMap[intro.reason] ?? "introspection_unavailable",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  const v = validateIntrospectionData(intro.data);
  if (!v.ok) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: (intro.data.kyc_tier as KycTier) ?? "tier_0",
      trust_score_used: intro.data.trust_score ?? 0,
      risk_flag_used: Boolean(intro.data.risk_flag),
      reason: v.reason,
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  if (v.sub !== body.user_id) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: v.kyc_tier,
      trust_score_used: v.trust_score,
      risk_flag_used: v.risk_flag,
      reason: "user_mismatch",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  const policy = evaluatePolicy(v.kyc_tier, v.trust_score, v.risk_flag);

  if (policy.decision === "reject") {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: v.kyc_tier,
      trust_score_used: v.trust_score,
      risk_flag_used: v.risk_flag,
      reason: policy.reason ?? "policy_reject",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  if (body.amount > policy.maxSingleTxn) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: v.kyc_tier,
      trust_score_used: v.trust_score,
      risk_flag_used: v.risk_flag,
      reason: "exceeds_single_transaction_limit",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  const dailyTotal = getDailyTotal(body.user_id);
  if (dailyTotal + body.amount > policy.dailyLimit) {
    const r: AuthorizeResponse = {
      decision: "rejected",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: v.kyc_tier,
      trust_score_used: v.trust_score,
      risk_flag_used: v.risk_flag,
      reason: "exceeds_daily_limit",
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  if (policy.decision === "allow_with_step_up" && policy.stepUpRequired) {
    const r: AuthorizeResponse = {
      decision: "step_up_required",
      amount: body.amount,
      currency: body.currency,
      kyc_tier_used: v.kyc_tier,
      trust_score_used: v.trust_score,
      risk_flag_used: v.risk_flag,
      reason: "trust_score_below_threshold",
      step_up_method: "otp",
      transaction_ref: `TXN-REF-${Date.now()}`,
      decision_timestamp: ts,
    };
    idempotency.set(body.idempotency_key, r);
    return r;
  }

  addDailySpend(body.user_id, body.amount);
  const r: AuthorizeResponse = {
    decision: "allowed",
    transaction_id: nextTxnId(),
    amount: body.amount,
    currency: body.currency,
    kyc_tier_used: v.kyc_tier,
    trust_score_used: v.trust_score,
    risk_flag_used: v.risk_flag,
    decision_timestamp: ts,
  };
  idempotency.set(body.idempotency_key, r);
  return r;
}

/** Test helpers */
export function resetPaymentState(): void {
  idempotency.clear();
  dailySpend.clear();
}
