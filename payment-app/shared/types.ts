export type KycTier = "tier_0" | "tier_1" | "tier_2";

export type TransactionDecision = "allowed" | "step_up_required" | "rejected";

export interface IntrospectionResult {
  active: boolean;
  sub?: string;
  scopes?: string[];
  client_id?: string;
  kyc_tier?: KycTier;
  trust_score?: number;
  risk_flag?: boolean;
  exp?: number;
  iss?: string;
}
