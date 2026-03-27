import type { KycTier } from "../shared/types";

export interface DemoUser {
  id: string;
  name: string;
  phone: string;
  kyc_tier: KycTier;
  trust_score: number;
  risk_flag: boolean;
}

/** Mirrors frontend mock users for demo `demo:<userId>` tokens. */
export const demoUsers: DemoUser[] = [
  { id: "usr_001", name: "Jane Smith", phone: "+1-555-0101", kyc_tier: "tier_2", trust_score: 82, risk_flag: false },
  { id: "usr_002", name: "Marcus Chen", phone: "+1-555-0102", kyc_tier: "tier_1", trust_score: 55, risk_flag: false },
  { id: "usr_003", name: "Anika Patel", phone: "+1-555-0103", kyc_tier: "tier_2", trust_score: 35, risk_flag: false },
  { id: "usr_004", name: "Leo Torres", phone: "+1-555-0104", kyc_tier: "tier_0", trust_score: 10, risk_flag: false },
  { id: "usr_005", name: "Sara Ivanova", phone: "+1-555-0105", kyc_tier: "tier_2", trust_score: 22, risk_flag: true },
];
