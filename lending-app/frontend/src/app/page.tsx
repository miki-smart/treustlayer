import Link from "next/link";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { ACCESS_COOKIE } from "@/lib/cookies";

export default async function Home() {
  const jar = await cookies();
  if (jar.get(ACCESS_COOKIE)?.value) {
    redirect("/loan");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-8 px-6 py-16">
      <div>
        <p className="text-sm font-medium tracking-wide text-[var(--muted)]">
          TrustIdLayer lending
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          Borrow with live trust and KYC
        </h1>
        <p className="mt-3 text-[var(--muted)] leading-relaxed">
          Sign in through TrustIdLayer. Every loan request runs a fresh token introspection —
          no stale scores, fail-closed if the platform is unreachable.
        </p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/login"
          className="inline-flex items-center justify-center rounded-lg bg-[var(--accent)] px-5 py-3 text-sm font-medium text-white transition hover:bg-[var(--accent-dim)]"
        >
          Sign in to apply
        </Link>
        <Link
          href="/loan"
          className="inline-flex items-center justify-center rounded-lg border border-[var(--border)] px-5 py-3 text-sm font-medium text-[var(--text)] transition hover:bg-[var(--surface)]"
        >
          Loan desk
        </Link>
      </div>
    </main>
  );
}
