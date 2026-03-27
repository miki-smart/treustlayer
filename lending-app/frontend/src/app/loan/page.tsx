import Link from "next/link";
import { LoanDesk } from "./loan-desk";

export default function LoanPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <Link href="/" className="text-sm text-[var(--muted)] hover:text-[var(--text)]">
        ← Home
      </Link>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight">Loan desk</h1>
      <p className="mt-2 text-[var(--muted)]">
        Tier-based limits with live <code className="text-[var(--accent)]">trust_score</code>,{" "}
        <code className="text-[var(--accent)]">kyc_tier</code>, and{" "}
        <code className="text-[var(--accent)]">risk_flag</code> from TrustIdLayer introspection.
      </p>
      <div className="mt-10">
        <LoanDesk />
      </div>
    </main>
  );
}
