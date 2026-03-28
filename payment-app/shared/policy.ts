import type { KycTier } from "./types";

export interface PolicyResult {
  maxSingleTxn: number;
  dailyLimit: number;
  stepUpRequired: boolean;
  decision: "reject" | "allow" | "allow_with_step_up";
  reason?: string;
}

export function evaluatePolicy(
  kyc_tier: KycTier,
  trust_score: number,
  risk_flag: boolean
): PolicyResult {
  if (kyc_tier === "tier_0") {
    return {
      maxSingleTxn: 0,
      dailyLimit: 0,
      stepUpRequired: false,
      decision: "reject",
      reason: "kyc_not_verified",
    };
  }
  if (risk_flag) {
    return {
      maxSingleTxn: 0,
      dailyLimit: 0,
      stepUpRequired: false,
      decision: "reject",
      reason: "risk_flag_active",
    };
  }

  if (kyc_tier === "tier_1") {
    if (trust_score <= 40) {
      return {
        maxSingleTxn: 0,
        dailyLimit: 0,
        stepUpRequired: false,
        decision: "reject",
        reason: "trust_score_too_low",
      };
    }
    if (trust_score <= 70) {
      return {
        maxSingleTxn: 100,
        dailyLimit: 200,
        stepUpRequired: true,
        decision: "allow_with_step_up",
      };
    }
    return {
      maxSingleTxn: 500,
      dailyLimit: 1000,
      stepUpRequired: false,
      decision: "allow",
    };
  }

  if (trust_score <= 40) {
    return {
      maxSingleTxn: 200,
      dailyLimit: 500,
      stepUpRequired: true,
      decision: "allow_with_step_up",
    };
  }
  if (trust_score <= 70) {
    return {
      maxSingleTxn: 1000,
      dailyLimit: 3000,
      stepUpRequired: false,
      decision: "allow",
    };
  }
  return {
    maxSingleTxn: 5000,
    dailyLimit: 15000,
    stepUpRequired: false,
    decision: "allow",
  };
}
