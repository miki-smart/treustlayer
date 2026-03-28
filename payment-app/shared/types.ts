import type { TrustIdLayerIdentityClaims } from "./trustidlayer-contract";

export type KycTier = "tier_0" | "tier_1" | "tier_2";

export type TransactionDecision = "allowed" | "step_up_required" | "rejected";

/** RFC 7662-style introspection body; when active, fields match TrustIdLayer JWT claims. */
export interface IntrospectionResult extends TrustIdLayerIdentityClaims {
  active: boolean;
}
