"use client";

import { useEffect, useState, useRef } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { decodeTrustLayerContext, type TrustLayerLaunchPayload } from "@/lib/trustlayerLaunchContext";

function BadgeCheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 0 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 0-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 0 0-6.76Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function TrustLayerLaunchBanner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [ctx, setCtx] = useState<TrustLayerLaunchPayload | null>(null);
  const processedRef = useRef(false);

  useEffect(() => {
    const raw = searchParams.get("trustlayer_ctx");
    if (!raw) return;
    if (processedRef.current) return;
    processedRef.current = true;
    const decoded = decodeTrustLayerContext(raw);
    if (decoded) setCtx(decoded);
    const next = new URLSearchParams(searchParams.toString());
    next.delete("trustlayer_ctx");
    const rest = next.toString();
    router.replace(rest ? `${pathname}?${rest}` : pathname, { scroll: false });
  }, [searchParams, router, pathname]);

  if (!ctx) return null;

  return (
    <div className="mb-6 rounded-lg border border-[var(--accent)]/30 bg-[var(--accent)]/5 px-4 py-3 text-sm">
      <div className="flex items-start gap-3">
        <BadgeCheckIcon className="h-5 w-5 shrink-0 text-[var(--accent)] mt-0.5" />
        <div className="space-y-1 min-w-0">
          <p className="font-medium text-[var(--text)]">Opened from TrustLayer</p>
          <p className="text-[var(--muted)] text-xs">
            KYC <span className="font-mono text-[var(--text)]">{ctx.kyc_level}</span>, trust score{" "}
            <span className="font-mono text-[var(--text)]">{ctx.trust_score}</span>
          </p>
          <p className="text-xs">
            <span className="text-[var(--muted)]">Name:</span> {ctx.full_name}{" "}
            <span className="text-[var(--muted)] ml-2">Email:</span> {ctx.email}
          </p>
        </div>
      </div>
    </div>
  );
}
