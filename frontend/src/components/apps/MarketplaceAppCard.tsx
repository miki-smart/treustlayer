import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { AppResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Globe,
  Copy,
  Check,
  Rocket,
  Link2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { deriveLaunchUrl } from "@/lib/marketplaceLaunch";
import { MarketplaceAppConsentDialog } from "@/components/apps/MarketplaceAppConsentDialog";

const scopeColors: Record<string, string> = {
  openid: "bg-blue-100 text-blue-800",
  profile: "bg-purple-100 text-purple-800",
  email: "bg-green-100 text-green-800",
  kyc_status: "bg-amber-100 text-amber-800",
  trust_score: "bg-orange-100 text-orange-800",
};

function ScopeTag({ scope }: { scope: string }) {
  const cls = scopeColors[scope] || "bg-muted text-muted-foreground";
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{scope}</span>;
}

type Props = {
  app: AppResponse;
  /** When set, show admin badges (optional) */
  variant?: "user" | "admin";
  onApprove?: (id: string) => void;
  onDeactivate?: (id: string) => void;
};

export function MarketplaceAppCard({ app, variant = "user", onApprove, onDeactivate }: Props) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [consentOpen, setConsentOpen] = useState(false);
  const launchUrl = deriveLaunchUrl(app);
  const copyId = () => {
    navigator.clipboard.writeText(app.client_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const openLaunchConsent = () => {
    if (!launchUrl) return;
    setConsentOpen(true);
  };

  const goToConnections = () => {
    navigate({ pathname: "/apps", search: "?tab=connections" });
  };

  return (
    <>
    {variant === "user" && (
      <MarketplaceAppConsentDialog app={app} open={consentOpen} onOpenChange={setConsentOpen} />
    )}
    <Card className="flex flex-col hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{app.name}</CardTitle>
            <CardDescription className="mt-0.5 line-clamp-2">{app.description || "No description"}</CardDescription>
          </div>
          {variant === "user" ? (
            <Badge variant="default" className="text-xs shrink-0">Approved</Badge>
          ) : (
            <div className="flex flex-col items-end gap-1 shrink-0">
              <Badge variant={app.is_approved ? "default" : "secondary"} className="text-xs">
                {app.is_approved ? "Approved" : "Pending"}
              </Badge>
              <Badge variant={app.is_active ? "outline" : "destructive"} className="text-xs">
                {app.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Globe className="h-3.5 w-3.5 shrink-0" />
          <code className="truncate max-w-[180px]">{app.client_id}</code>
          <button type="button" onClick={copyId} className="hover:text-foreground transition-colors">
            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
          </button>
        </div>
        {app.allowed_scopes?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {(variant === "user" ? app.allowed_scopes.slice(0, 6) : app.allowed_scopes.slice(0, 4)).map((s) => (
              <ScopeTag key={s} scope={s} />
            ))}
            {variant === "admin" && app.allowed_scopes.length > 4 && (
              <span className="text-xs text-muted-foreground">+{app.allowed_scopes.length - 4}</span>
            )}
          </div>
        )}
        <div className="flex flex-col gap-2 pt-1 border-t border-border/60">
          <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            Open &amp; access
          </p>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
            <Button
              type="button"
              size="sm"
              className="h-9 flex-1 gap-2 text-xs font-semibold"
              disabled={!launchUrl}
              title={
                launchUrl
                  ? variant === "user"
                    ? "Review permissions and consent before opening the app"
                    : `Open ${launchUrl}`
                  : "No redirect URI — cannot open app"
              }
              onClick={variant === "user" ? openLaunchConsent : () => {
                if (!launchUrl) return;
                window.open(launchUrl, "_blank", "noopener,noreferrer");
              }}
            >
              <Rocket className="h-4 w-4 shrink-0" aria-hidden />
              Launch
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-9 flex-1 gap-2 text-xs font-semibold"
              title="Manage OAuth access and active sessions for your apps"
              onClick={goToConnections}
            >
              <Link2 className="h-4 w-4 shrink-0" aria-hidden />
              Connect
            </Button>
          </div>
          {(onApprove || onDeactivate) && (
            <div className="flex flex-col gap-2 pt-2 border-t sm:flex-row sm:flex-wrap">
              {onApprove && !app.is_approved && (
                <Button size="sm" className="h-8 text-xs w-full sm:w-auto sm:min-w-[7rem] sm:flex-1" onClick={() => onApprove(app.id)}>
                  <CheckCircle2 className="h-3 w-3 mr-1 shrink-0" /> Approve
                </Button>
              )}
              {onDeactivate && app.is_active && (
                <Button size="sm" variant="destructive" className="h-8 text-xs w-full sm:w-auto sm:min-w-[7rem] sm:flex-1" onClick={() => onDeactivate(app.id)}>
                  <XCircle className="h-3 w-3 mr-1 shrink-0" /> Deactivate
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
    </>
  );
}
