import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Zap, Activity } from "lucide-react";
import { StatsCards } from "@/components/StatsCards";
import { PaymentForm } from "@/components/PaymentForm";
import { TransactionTable } from "@/components/TransactionTable";
import { PolicyTable } from "@/components/PolicyTable";
import { mockTransactionHistory, type TransactionResponse } from "@/lib/trustid";
import { fetchApiHealth } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { IdentityFromIdpDialog } from "@/components/IdentityFromIdpDialog";
import { TrustLayerLaunchBanner } from "@/components/TrustLayerLaunchBanner";

const Index = () => {
  const [transactions, setTransactions] = useState<TransactionResponse[]>(mockTransactionHistory);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [apiMock, setApiMock] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    fetchApiHealth().then((h) => {
      setApiOk(h.ok);
      setApiMock(h.mock);
    });
  }, []);

  const handleTransaction = (txn: TransactionResponse) => {
    setTransactions((prev) => [txn, ...prev]);
  };

  const approved = transactions.filter((t) => t.decision === "allowed").length;
  const rejected = transactions.filter((t) => t.decision === "rejected").length;
  const stepUps = transactions.filter((t) => t.decision === "step_up_required").length;
  const totalProcessed = transactions.reduce((sum, t) => sum + (t.decision === "allowed" ? t.amount : 0), 0);

  return (
    <div className="min-h-screen bg-background">
      <IdentityFromIdpDialog />
      <header className="border-b border-border">
        <div className="container max-w-7xl mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center glow-primary">
              <Shield size={18} className="text-primary" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">PaymentApp</h1>
              <p className="text-xs text-muted-foreground">TrustIdLayer Integration</p>
            </div>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${
                apiOk ? "bg-success/10 border-success/20" : "bg-muted border-border"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${apiOk ? "bg-success animate-pulse-glow" : "bg-muted-foreground"}`}
              />
              <span className={`text-xs font-medium ${apiOk ? "text-success" : "text-muted-foreground"}`}>
                {apiOk === null ? "API…" : apiOk ? "API up" : "API down"}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <Activity size={14} />
              <span>
                Backend: {apiMock === undefined ? "…" : apiMock ? "mock introspect" : "live introspect"}
              </span>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/login">Sign in</Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="container max-w-7xl mx-auto px-6 py-8 space-y-8">
        <TrustLayerLaunchBanner />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-2 mb-1">
            <Zap size={16} className="text-primary" />
            <span className="text-xs text-primary font-medium uppercase tracking-wider">Real-Time Enforcement</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-1">Transaction Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            Payments call the Express API: introspection, policy, daily caps, and idempotency before a decision.
          </p>
        </motion.div>

        <StatsCards
          totalProcessed={totalProcessed}
          approved={approved}
          rejected={rejected}
          stepUps={stepUps}
        />

        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2">
            <PaymentForm onTransaction={handleTransaction} />
          </div>
          <div className="lg:col-span-3">
            <TransactionTable transactions={transactions} />
          </div>
        </div>

        <PolicyTable />
      </main>
    </div>
  );
};

export default Index;
