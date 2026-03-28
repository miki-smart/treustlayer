import { Shield, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

interface TrustScoreGaugeProps {
  score: number;
  size?: "sm" | "lg";
}

export function TrustScoreGauge({ score, size = "lg" }: TrustScoreGaugeProps) {
  const radius = size === "lg" ? 70 : 36;
  const stroke = size === "lg" ? 8 : 5;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const center = radius + stroke;
  const dim = center * 2;

  const color =
    score >= 71 ? "hsl(var(--success))" :
    score >= 41 ? "hsl(var(--warning))" :
    "hsl(var(--destructive))";

  const label = score >= 71 ? "High" : score >= 41 ? "Medium" : "Low";
  const Icon = score >= 71 ? TrendingUp : score >= 41 ? AlertTriangle : TrendingDown;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={dim} height={dim} className="transform -rotate-90">
        <circle cx={center} cy={center} r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth={stroke} />
        <motion.circle
          cx={center} cy={center} r={radius} fill="none"
          stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - progress }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center" style={{ marginTop: size === "lg" ? 28 : 10 }}>
        <span className={`font-mono font-bold ${size === "lg" ? "text-3xl" : "text-base"}`} style={{ color }}>
          {score}
        </span>
        {size === "lg" && (
          <span className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            <Icon size={12} /> {label}
          </span>
        )}
      </div>
    </div>
  );
}

interface KycBadgeProps {
  tier: string;
}

export function KycBadge({ tier }: KycBadgeProps) {
  const config: Record<string, { label: string; className: string }> = {
    tier_0: { label: "Unverified", className: "bg-destructive/15 text-destructive border-destructive/20" },
    tier_1: { label: "Basic KYC", className: "bg-warning/15 text-warning border-warning/20" },
    tier_2: { label: "Full KYC", className: "bg-success/15 text-success border-success/20" },
  };

  const { label, className } = config[tier] || config.tier_0;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${className}`}>
      <Shield size={12} />
      {label}
    </span>
  );
}

interface DecisionBadgeProps {
  decision: string;
}

export function DecisionBadge({ decision }: DecisionBadgeProps) {
  const config: Record<string, { label: string; className: string }> = {
    allowed: { label: "Allowed", className: "bg-success/15 text-success border-success/20" },
    step_up_required: { label: "Step-Up", className: "bg-warning/15 text-warning border-warning/20" },
    rejected: { label: "Rejected", className: "bg-destructive/15 text-destructive border-destructive/20" },
  };

  const { label, className } = config[decision] || { label: decision, className: "bg-muted text-muted-foreground border-border" };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${className}`}>
      {label}
    </span>
  );
}
