import { motion } from "framer-motion";
import { DollarSign, ShieldCheck, Activity, XCircle } from "lucide-react";

interface StatsCardsProps {
  totalProcessed: number;
  approved: number;
  rejected: number;
  stepUps: number;
}

const cards = [
  { key: "processed" as const, label: "Processed", icon: DollarSign, format: (v: number) => `$${v.toLocaleString()}`, colorClass: "text-foreground" },
  { key: "approved" as const, label: "Approved", icon: ShieldCheck, format: (v: number) => String(v), colorClass: "text-success" },
  { key: "stepUps" as const, label: "Step-Ups", icon: Activity, format: (v: number) => String(v), colorClass: "text-warning" },
  { key: "rejected" as const, label: "Rejected", icon: XCircle, format: (v: number) => String(v), colorClass: "text-destructive" },
];

export function StatsCards({ totalProcessed, approved, rejected, stepUps }: StatsCardsProps) {
  const values: Record<string, number> = { processed: totalProcessed, approved, rejected, stepUps };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, duration: 0.4 }}
          className="card-elevated p-5"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-muted-foreground uppercase tracking-wider">{card.label}</span>
            <card.icon size={16} className="text-muted-foreground" />
          </div>
          <p className={`text-2xl font-bold font-mono ${card.colorClass || "text-foreground"}`}>
            {card.format(values[card.key])}
          </p>
        </motion.div>
      ))}
    </div>
  );
}
