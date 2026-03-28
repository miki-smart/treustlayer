import { motion } from "framer-motion";
import { Shield, Check, X } from "lucide-react";
import { evaluatePolicy } from "@/lib/trustid";
import type { KycTier } from "@/lib/trustid";

const policyRows: Array<{
  tier: KycTier;
  scoreRange: string;
  riskFlag: boolean;
  scoreExample: number;
}> = [
  { tier: "tier_0", scoreRange: "Any", riskFlag: false, scoreExample: 10 },
  { tier: "tier_1", scoreRange: "0–40", riskFlag: false, scoreExample: 30 },
  { tier: "tier_1", scoreRange: "41–70", riskFlag: false, scoreExample: 55 },
  { tier: "tier_1", scoreRange: "71–100", riskFlag: false, scoreExample: 85 },
  { tier: "tier_2", scoreRange: "0–40", riskFlag: false, scoreExample: 30 },
  { tier: "tier_2", scoreRange: "41–70", riskFlag: false, scoreExample: 55 },
  { tier: "tier_2", scoreRange: "71–100", riskFlag: false, scoreExample: 85 },
];

export function PolicyTable() {
  return (
    <div className="card-elevated overflow-hidden">
      <div className="p-5 border-b border-border flex items-center gap-2">
        <Shield size={18} className="text-primary" />
        <div>
          <h2 className="text-lg font-semibold">Transaction Policy Matrix</h2>
          <p className="text-sm text-muted-foreground">Live enforcement rules from TrustIdLayer</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted-foreground uppercase tracking-wider">
              <th className="text-left p-4">KYC Tier</th>
              <th className="text-left p-4">Trust Score</th>
              <th className="text-left p-4">Max Txn</th>
              <th className="text-left p-4">Daily Limit</th>
              <th className="text-left p-4">Step-Up</th>
              <th className="text-left p-4">Decision</th>
            </tr>
          </thead>
          <tbody>
            {policyRows.map((row, i) => {
              const policy = evaluatePolicy(row.tier, row.scoreExample, row.riskFlag);
              return (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                >
                  <td className="p-4 font-mono text-xs">{row.tier}</td>
                  <td className="p-4 font-mono text-xs">{row.scoreRange}</td>
                  <td className="p-4 font-mono font-medium">
                    {policy.maxSingleTxn > 0 ? `$${policy.maxSingleTxn.toLocaleString()}` : "—"}
                  </td>
                  <td className="p-4 font-mono font-medium">
                    {policy.dailyLimit > 0 ? `$${policy.dailyLimit.toLocaleString()}` : "—"}
                  </td>
                  <td className="p-4">
                    {policy.stepUpRequired ? (
                      <span className="text-warning text-xs flex items-center gap-1"><Check size={12} /> OTP</span>
                    ) : (
                      <span className="text-muted-foreground text-xs"><X size={12} /></span>
                    )}
                  </td>
                  <td className="p-4">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      policy.decision === "allow" ? "bg-success/15 text-success" :
                      policy.decision === "allow_with_step_up" ? "bg-warning/15 text-warning" :
                      "bg-destructive/15 text-destructive"
                    }`}>
                      {policy.decision === "allow" ? "Allow" :
                       policy.decision === "allow_with_step_up" ? "Step-Up" : "Reject"}
                    </span>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
