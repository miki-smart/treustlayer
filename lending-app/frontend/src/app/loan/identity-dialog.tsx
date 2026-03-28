"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

/**
 * One-time modal after OAuth/password sign-in when URL has ?identity=1 — shows IdP introspection payload.
 */
export function LoanIdentityDialog() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const show = searchParams.get("identity") === "1";
  const [open, setOpen] = useState(false);
  const [json, setJson] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!show) return;
    let cancelled = false;
    (async () => {
      const res = await fetch("/api/auth/identity-context");
      const data = await res.json().catch(() => ({}));
      if (cancelled) return;
      if (!res.ok) {
        setErr(typeof data.error === "string" ? data.error : "failed");
        setOpen(true);
        return;
      }
      setJson(JSON.stringify(data, null, 2));
      setOpen(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [show]);

  if (!show) return null;

  const close = () => {
    setOpen(false);
    router.replace("/loan");
  };

  if (!open) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
        <p className="text-sm text-[var(--muted)]">Loading identity from TrustIdLayer…</p>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="identity-dialog-title"
    >
      <div className="max-h-[85vh] w-full max-w-lg overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-lg">
        <div className="border-b border-[var(--border)] px-5 py-4">
          <h2 id="identity-dialog-title" className="text-lg font-semibold tracking-tight">
            Identity from TrustIdLayer
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Introspection response for your access token (same fields as the IdP JWT claims).
          </p>
        </div>
        <div className="max-h-[55vh] overflow-auto px-5 py-4">
          {err ? (
            <p className="text-sm text-[var(--danger)]">{err}</p>
          ) : (
            <pre className="whitespace-pre-wrap break-all text-xs font-mono text-[var(--text)]">{json ?? "…"}</pre>
          )}
        </div>
        <div className="flex justify-end border-t border-[var(--border)] px-5 py-3">
          <button
            type="button"
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-dim)]"
            onClick={close}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
