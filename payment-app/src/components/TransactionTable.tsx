import { motion } from "framer-motion";
import { DecisionBadge, KycBadge } from "@/components/TrustIndicators";
import type { TransactionResponse } from "@/lib/trustid";

interface TransactionTableProps {
  transactions: TransactionResponse[];
}

export function TransactionTable({ transactions }: TransactionTableProps) {
  return (
    <div className="card-elevated overflow-hidden">
      <div className="p-5 border-b border-border">
        <h2 className="text-lg font-semibold">Transaction History</h2>
        <p className="text-sm text-muted-foreground">Real-time introspection audit log</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted-foreground uppercase tracking-wider">
              <th className="text-left p-4">Time</th>
              <th className="text-left p-4">Amount</th>
              <th className="text-left p-4">KYC Tier</th>
              <th className="text-left p-4">Trust Score</th>
              <th className="text-left p-4">Risk</th>
              <th className="text-left p-4">Decision</th>
              <th className="text-left p-4">Reason</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn, i) => (
              <motion.tr
                key={txn.decision_timestamp + i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border-b border-border/50 hover:bg-muted/30 transition-colors"
              >
                <td className="p-4 font-mono text-xs text-muted-foreground">
                  {new Date(txn.decision_timestamp).toLocaleTimeString()}
                </td>
                <td className="p-4 font-mono font-medium">
                  ${txn.amount.toLocaleString()}
                </td>
                <td className="p-4">
                  <KycBadge tier={txn.kyc_tier_used} />
                </td>
                <td className="p-4">
                  <span className={`font-mono font-bold ${
                    txn.trust_score_used >= 71 ? "text-success" :
                    txn.trust_score_used >= 41 ? "text-warning" : "text-destructive"
                  }`}>
                    {txn.trust_score_used}
                  </span>
                </td>
                <td className="p-4">
                  {txn.risk_flag_used ? (
                    <span className="text-destructive text-xs font-medium">⚠ Yes</span>
                  ) : (
                    <span className="text-muted-foreground text-xs">No</span>
                  )}
                </td>
                <td className="p-4">
                  <DecisionBadge decision={txn.decision} />
                </td>
                <td className="p-4 text-xs text-muted-foreground font-mono">
                  {txn.reason || "—"}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
