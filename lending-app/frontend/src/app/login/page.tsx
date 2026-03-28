"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

function oauthErrorMessage(code: string): string {
  if (code === "oauth_not_configured") {
    return "Browser sign-in is not configured. Set TRUSTIDLAYER_OAUTH_AUTHORIZE_URL (or BASE_URL + path) and CLIENT_ID, or use password sign-in.";
  }
  if (code === "invalid_oauth_state") {
    return "Sign-in session expired or invalid. Try again.";
  }
  return code.replace(/\+/g, " ");
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryError = searchParams.get("error");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(
    queryError ? oauthErrorMessage(queryError) : null,
  );
  const [loading, setLoading] = useState(false);
  const [oauthStarting, setOauthStarting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(typeof data.error === "string" ? data.error : "Sign-in failed");
        return;
      }
      router.push(typeof data.redirect === "string" ? data.redirect : "/loan");
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-16">
      <Link
        href="/"
        className="mb-8 text-sm text-[var(--muted)] hover:text-[var(--text)]"
      >
        ← Back
      </Link>
      <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
      <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
        Use TrustIdLayer in the browser, or sign in with a password on your server (authorization
        code + PKCE). The <code className="text-[var(--accent)]">client_secret</code> never reaches
        the browser.
      </p>

      <div className="mt-8 flex flex-col gap-3">
        <a
          href="/api/auth/oauth/start"
          onClick={() => setOauthStarting(true)}
          className="inline-flex items-center justify-center rounded-lg bg-[var(--accent)] py-3 text-sm font-medium text-white transition hover:bg-[var(--accent-dim)]"
        >
          {oauthStarting ? "Redirecting…" : "Sign in with TrustIdLayer"}
        </a>
        <p className="text-center text-xs text-[var(--muted)]">
          Opens TrustIdLayer to sign in, then returns here to complete the code exchange.
        </p>
      </div>

      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center" aria-hidden>
          <div className="w-full border-t border-[var(--border)]" />
        </div>
        <div className="relative flex justify-center text-xs uppercase tracking-wide">
          <span className="bg-[var(--bg)] px-3 text-[var(--muted)]">Or</span>
        </div>
      </div>

      <p className="text-sm text-[var(--muted)] leading-relaxed">
        Password sign-in: your server calls{" "}
        <code className="text-[var(--accent)]">/auth/authorize</code> and exchanges the code.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-[var(--muted)]">Username</span>
          <input
            autoComplete="username"
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-[var(--text)] outline-none ring-[var(--accent)] focus:ring-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="text-[var(--muted)]">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-[var(--text)] outline-none ring-[var(--accent)] focus:ring-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error ? (
          <p className="rounded-lg border border-red-900/50 bg-red-950/30 px-3 py-2 text-sm text-[var(--danger)]">
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={loading}
          className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] py-3 text-sm font-medium text-[var(--text)] transition hover:bg-[var(--bg)] disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in with password"}
        </button>
      </form>

      <p className="mt-8 text-xs text-[var(--muted)] leading-relaxed">
        <strong className="text-[var(--text)]">Mock mode:</strong> set{" "}
        <code className="text-[var(--accent)]">TRUSTIDLAYER_MOCK=true</code>. Users{" "}
        <code className="text-[var(--accent)]">riskuser</code> and{" "}
        <code className="text-[var(--accent)]">inactive</code> exercise risk-flag and inactive
        token paths.
      </p>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-16 text-sm text-[var(--muted)]">
          Loading…
        </main>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
