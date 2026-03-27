"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

type Preview =
  | { loading: true }
  | { loading: false; error: string }
  | {
      loading: false;
      error?: undefined;
      kyc_tier: string;
      trust_score: number;
      risk_flag: boolean;
      decision: string;
      max_lendable_usd: number;
      reason_code: string | null;
      eligible: boolean;
      lending_engine: string;
      trust_band?: number;
      apr_annual_percent?: number | null;
      max_term_days?: number;
      offer_label?: string;
    };

/** Matches backend/app/lending_engine.py matrix (trust_score 0–100 → band). */
const trustBandRows = [
  {
    band: "0",
    range: "0–33",
    eligible: false,
    max: "—",
    apr: "—",
    term: "—",
  },
  {
    band: "1",
    range: "34–66",
    eligible: true,
    max: "$3,500",
    apr: "15.9%",
    term: "180 days",
  },
  {
    band: "2",
    range: "67–100",
    eligible: true,
    max: "$15,000",
    apr: "10.5%",
    term: "365 days",
  },
];

export function LoanDesk() {
  const router = useRouter();
  const [preview, setPreview] = useState<Preview>({ loading: true });
  const [amount, setAmount] = useState("1000");
  const [termDays, setTermDays] = useState("30");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<unknown>(null);

  const loadPreview = useCallback(async () => {
    setPreview({ loading: true });
    const res = await fetch("/api/loan/preview");
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      setPreview({ loading: false, error: "not_authenticated" });
      return;
    }
    if (!res.ok) {
      setPreview({
        loading: false,
        error: typeof data.error === "string" ? data.error : "preview_failed",
      });
      return;
    }
    setPreview({
      loading: false,
      kyc_tier: data.kyc_tier,
      trust_score: data.trust_score,
      risk_flag: data.risk_flag,
      decision: data.decision,
      max_lendable_usd: data.max_lendable_usd,
      reason_code: data.reason_code ?? null,
      eligible: Boolean(data.eligible),
      lending_engine:
        typeof data.lending_engine === "string" ? data.lending_engine : "next_policy",
      trust_band: typeof data.trust_band === "number" ? data.trust_band : undefined,
      apr_annual_percent:
        typeof data.apr_annual_percent === "number"
          ? data.apr_annual_percent
          : data.apr_annual_percent === null
            ? null
            : undefined,
      max_term_days: typeof data.max_term_days === "number" ? data.max_term_days : undefined,
      offer_label: typeof data.offer_label === "string" ? data.offer_label : undefined,
    });
  }, []);

  useEffect(() => {
    void loadPreview();
  }, [loadPreview]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  async function submitLoan(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      const res = await fetch("/api/loan/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requested_amount: Number(amount),
          currency: "USD",
          loan_term_days: Number(termDays),
        }),
      });
      const data = await res.json().catch(() => ({}));
      setResult(data);
      await loadPreview();
    } finally {
      setSubmitting(false);
    }
  }

  if (preview.loading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-10 text-center text-[var(--muted)]">
        Loading eligibility (TrustIdLayer + lending engine)…
      </div>
    );
  }

  if ("error" in preview && preview.error === "not_authenticated") {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
        <p className="text-[var(--muted)]">You need to sign in first.</p>
        <Link
          href="/login"
          className="mt-4 inline-block rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white"
        >
          Sign in
        </Link>
      </div>
    );
  }

  if ("error" in preview) {
    return (
      <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-6">
        <p className="font-medium text-[var(--warning)]">Eligibility unavailable</p>
        <p className="mt-2 text-sm text-[var(--muted)]">
          {preview.error} — we fail closed and do not show cached trust data beyond TTL.
        </p>
        <button
          type="button"
          onClick={() => void loadPreview()}
          className="mt-4 rounded-lg border border-[var(--border)] px-4 py-2 text-sm hover:bg-[var(--surface)]"
        >
          Retry introspection
        </button>
      </div>
    );
  }

  const max = preview.max_lendable_usd;

  return (
    <div className="flex flex-col gap-10">
      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Live offer</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              TrustIdLayer introspection on each request; limits and APR from the{" "}
              <span className="font-mono text-[var(--accent)]">
                {preview.lending_engine === "fastapi" ? "FastAPI" : "Next.js"}
              </span>{" "}
              lending engine when configured.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void loadPreview()}
              className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--bg)]"
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => void logout()}
              className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--bg)]"
            >
              Sign out
            </button>
          </div>
        </div>

        <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">KYC tier</dt>
            <dd className="mt-1 font-mono text-lg">{preview.kyc_tier}</dd>
          </div>
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Trust score</dt>
            <dd className="mt-1 font-mono text-lg">{preview.trust_score}</dd>
          </div>
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Trust band</dt>
            <dd className="mt-1 font-mono text-lg">
              {preview.trust_band !== undefined ? preview.trust_band : "—"}
            </dd>
          </div>
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Risk flag</dt>
            <dd className="mt-1 text-lg">{preview.risk_flag ? "Yes" : "No"}</dd>
          </div>
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">APR (annual)</dt>
            <dd className="mt-1 font-mono text-lg">
              {preview.apr_annual_percent != null ? `${preview.apr_annual_percent}%` : "—"}
            </dd>
          </div>
          <div className="rounded-lg bg-[var(--bg)] p-4">
            <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">Max term</dt>
            <dd className="mt-1 font-mono text-lg">
              {preview.max_term_days != null ? `${preview.max_term_days} days` : "—"}
            </dd>
          </div>
        </dl>
        {preview.offer_label ? (
          <p className="mt-4 text-sm text-[var(--muted)]">
            Offer tier:{" "}
            <span className="font-medium text-[var(--text)]">{preview.offer_label}</span>
          </p>
        ) : null}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              preview.eligible
                ? "bg-emerald-950/50 text-[var(--success)]"
                : "bg-[var(--bg)] text-[var(--muted)]"
            }`}
          >
            Policy: {preview.decision.replaceAll("_", " ")}
          </span>
          {preview.eligible ? (
            <span className="text-sm text-[var(--muted)]">
              Max lendable now:{" "}
              <strong className="text-[var(--text)]">${max.toLocaleString()}</strong> USD
            </span>
          ) : (
            <span className="text-sm text-[var(--muted)]">
              {preview.reason_code
                ? `Reason: ${preview.reason_code.replace(/_/g, " ")}`
                : "Not eligible for instant approval"}
            </span>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-lg font-semibold">Trust score → band matrix</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Raw trust score (0–100) maps to band 0, 1, or 2.{" "}
          <code className="text-[var(--accent)]">tier_0</code> or a risk flag still blocks
          lending regardless of band. Same matrix is enforced in{" "}
          <code className="text-[var(--accent)]">backend/app/lending_engine.py</code>.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-[var(--muted)]">
                <th className="py-2 pr-4 font-medium">Band</th>
                <th className="py-2 pr-4 font-medium">Score range</th>
                <th className="py-2 pr-4 font-medium">Eligible</th>
                <th className="py-2 pr-4 font-medium">Max principal</th>
                <th className="py-2 pr-4 font-medium">APR</th>
                <th className="py-2 pr-4 font-medium">Max term</th>
              </tr>
            </thead>
            <tbody>
              {trustBandRows.map((r) => (
                <tr
                  key={r.band}
                  className={`border-b border-[var(--border)]/60 ${
                    preview.trust_band !== undefined && String(preview.trust_band) === r.band
                      ? "bg-[var(--accent)]/10"
                      : ""
                  }`}
                >
                  <td className="py-3 pr-4 font-mono text-xs">{r.band}</td>
                  <td className="py-3 pr-4 font-mono text-xs">{r.range}</td>
                  <td className="py-3 pr-4">{r.eligible ? "Yes" : "No"}</td>
                  <td className="py-3 pr-4 text-[var(--muted)]">{r.max}</td>
                  <td className="py-3 pr-4 text-[var(--muted)]">{r.apr}</td>
                  <td className="py-3 pr-4 text-[var(--muted)]">{r.term}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-lg font-semibold">Request a loan</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Submits to <code className="text-[var(--accent)]">POST /api/loan/request</code> — server
          introspects your token, then calls the lending engine (FastAPI when{" "}
          <code className="text-[var(--accent)]">LENDING_API_URL</code> is set).
        </p>
        <form onSubmit={(e) => void submitLoan(e)} className="mt-6 grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">Amount (USD)</span>
            <input
              type="number"
              min={1}
              step={1}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 font-mono outline-none ring-[var(--accent)] focus:ring-2"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">Term (days)</span>
            <input
              type="number"
              min={1}
              step={1}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 font-mono outline-none ring-[var(--accent)] focus:ring-2"
              value={termDays}
              onChange={(e) => setTermDays(e.target.value)}
            />
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-[var(--accent)] py-3 text-sm font-medium text-white hover:bg-[var(--accent-dim)] disabled:opacity-50 sm:w-auto sm:px-8"
            >
              {submitting ? "Deciding…" : "Submit loan request"}
            </button>
          </div>
        </form>

        {result ? (
          <pre className="mt-6 max-h-64 overflow-auto rounded-lg bg-[var(--bg)] p-4 text-xs leading-relaxed text-[var(--muted)]">
            {JSON.stringify(result, null, 2)}
          </pre>
        ) : null}
      </section>
    </div>
  );
}
