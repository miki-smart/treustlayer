import { useEffect, useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { BadgeCheck } from "lucide-react";
import { decodeTrustLayerContext, type TrustLayerLaunchPayload } from "@/lib/trustlayerLaunchContext";

/**
 * Reads `?trustlayer_ctx=` from the dashboard URL (IdP marketplace launch), shows a summary, then strips the query.
 */
export function TrustLayerLaunchBanner() {
  const location = useLocation();
  const navigate = useNavigate();
  const [ctx, setCtx] = useState<TrustLayerLaunchPayload | null>(null);
  const processedRef = useRef(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const raw = params.get("trustlayer_ctx");
    if (!raw) return;
    if (processedRef.current) return;
    processedRef.current = true;
    const decoded = decodeTrustLayerContext(raw);
    if (decoded) setCtx(decoded);
    params.delete("trustlayer_ctx");
    const next = `${location.pathname}${params.toString() ? `?${params.toString()}` : ""}${location.hash}`;
    navigate(next, { replace: true });
  }, [location.pathname, location.search, location.hash, navigate]);

  if (!ctx) return null;

  return (
    <div className="mb-6 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 text-sm">
      <div className="flex items-start gap-3">
        <BadgeCheck className="h-5 w-5 shrink-0 text-primary mt-0.5" />
        <div className="space-y-1 min-w-0">
          <p className="font-medium text-foreground">Signed in from TrustLayer</p>
          <p className="text-muted-foreground text-xs">
            Context passed for this session: KYC <span className="font-mono text-foreground">{ctx.kyc_level}</span>, trust score{" "}
            <span className="font-mono text-foreground">{ctx.trust_score}</span>
          </p>
          <p className="text-xs">
            <span className="text-muted-foreground">Name:</span> {ctx.full_name}{" "}
            <span className="text-muted-foreground ml-2">Email:</span> {ctx.email}
          </p>
        </div>
      </div>
    </div>
  );
}
