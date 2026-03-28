import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { KycBadge, DecisionBadge } from "@/components/TrustIndicators";
import { mockUsers, type TransactionResponse } from "@/lib/trustid";
import { authorizePayment } from "@/lib/api";
import { getAccessToken } from "@/lib/session";

interface PaymentFormProps {
  onTransaction: (txn: TransactionResponse) => void;
}

export function PaymentForm({ onTransaction }: PaymentFormProps) {
  const [selectedUser, setSelectedUser] = useState(mockUsers[0].id);
  const [amount, setAmount] = useState("");
  const [recipient, setRecipient] = useState("merchant_001");
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<TransactionResponse | null>(null);
  const [step, setStep] = useState<string>("");

  const user = mockUsers.find((u) => u.id === selectedUser)!;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) return;

    setProcessing(true);
    setResult(null);

    const sessionToken = getAccessToken();
    const user_access_token = sessionToken ?? `demo:${selectedUser}`;

    setStep("Validating access token…");
    await delay(200);

    setStep("Calling POST /api/v1/auth/introspect (server)…");
    await delay(200);

    setStep("Evaluating transaction policy…");

    try {
      const response = await authorizePayment({
        user_id: selectedUser,
        amount: parseFloat(amount),
        currency: "USD",
        recipient_id: recipient,
        transaction_type: "purchase",
        idempotency_key: crypto.randomUUID(),
        user_access_token,
      });

      setStep("");
      setResult(response);
      onTransaction(response);
    } catch (err) {
      setStep("");
      const message = err instanceof Error ? err.message : "request_failed";
      const fallback: TransactionResponse = {
        decision: "rejected",
        amount: parseFloat(amount),
        currency: "USD",
        kyc_tier_used: user.kyc_tier,
        trust_score_used: user.trust_score,
        risk_flag_used: user.risk_flag,
        reason: message,
        decision_timestamp: new Date().toISOString(),
      };
      setResult(fallback);
      onTransaction(fallback);
    } finally {
      setProcessing(false);
    }
  };

  const ResultIcon =
    result?.decision === "allowed"
      ? CheckCircle2
      : result?.decision === "step_up_required"
        ? AlertTriangle
        : XCircle;
  const resultColor =
    result?.decision === "allowed"
      ? "text-success"
      : result?.decision === "step_up_required"
        ? "text-warning"
        : "text-destructive";

  return (
    <div className="card-elevated p-6">
      <h2 className="text-lg font-semibold mb-1">New Transaction</h2>
      <p className="text-sm text-muted-foreground mb-5">
        Authorize via backend: introspection, policy, daily limits, idempotency.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs text-muted-foreground uppercase tracking-wider mb-1.5 block">Payer</label>
          <Select value={selectedUser} onValueChange={setSelectedUser}>
            <SelectTrigger className="bg-muted border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {mockUsers.map((u) => (
                <SelectItem key={u.id} value={u.id}>
                  <span className="flex items-center gap-2">
                    {u.name}
                    <KycBadge tier={u.kyc_tier} />
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="text-xs text-muted-foreground uppercase tracking-wider mb-1.5 block">
              Amount (USD)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
              <Input
                type="number"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="pl-7 bg-muted border-border font-mono"
                min="0.01"
                step="0.01"
              />
            </div>
          </div>
          <div className="flex-1">
            <label className="text-xs text-muted-foreground uppercase tracking-wider mb-1.5 block">Recipient</label>
            <Input
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="bg-muted border-border font-mono text-sm"
            />
          </div>
        </div>

        <div className="flex items-center gap-4 p-3 rounded-md bg-muted/50 border border-border/50">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Score:</span>
            <span
              className={`font-mono font-bold text-sm ${
                user.trust_score >= 71 ? "text-success" : user.trust_score >= 41 ? "text-warning" : "text-destructive"
              }`}
            >
              {user.trust_score}
            </span>
          </div>
          <KycBadge tier={user.kyc_tier} />
          {user.risk_flag && (
            <span className="text-xs text-destructive flex items-center gap-1">
              <AlertTriangle size={12} /> Risk flagged
            </span>
          )}
        </div>

        <p className="text-xs text-muted-foreground">
          Token: {getAccessToken() ? "session from Sign in" : `demo:${selectedUser} (or sign in)`}
        </p>

        <Button
          type="submit"
          disabled={processing || !amount}
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
        >
          {processing ? (
            <span className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" /> Processing…
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Send size={16} /> Authorize Payment
            </span>
          )}
        </Button>
      </form>

      <AnimatePresence>
        {step && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-3 rounded-md bg-muted/50 border border-border/50"
          >
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 size={14} className="animate-spin text-primary" />
              {step}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 rounded-md bg-muted/50 border border-border/50"
          >
            <div className="flex items-center gap-2 mb-3">
              <ResultIcon size={18} className={resultColor} />
              <span className={`font-semibold ${resultColor}`}>
                {result.decision === "allowed"
                  ? "Transaction Approved"
                  : result.decision === "step_up_required"
                    ? "Step-Up Required"
                    : "Transaction Rejected"}
              </span>
              <DecisionBadge decision={result.decision} />
            </div>
            <div className="space-y-1 text-xs font-mono text-muted-foreground">
              {result.transaction_id && <div>ID: {result.transaction_id}</div>}
              {result.transaction_ref && <div>Ref: {result.transaction_ref}</div>}
              {result.reason && <div>Reason: {result.reason}</div>}
              {result.step_up_method && <div>Method: {result.step_up_method}</div>}
              <div>
                Amount: ${result.amount} {result.currency}
              </div>
              <div>
                KYC: {result.kyc_tier_used} | Score: {result.trust_score_used} | Risk: {String(result.risk_flag_used)}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
