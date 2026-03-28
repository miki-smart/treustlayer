import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AppResponse } from "@/services/api";
import { authApi, consentApi, trustApi } from "@/services/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { openLaunchDashboardInNewTab } from "@/lib/launchDownstreamDashboard";
import { deriveAppOrigin } from "@/lib/marketplaceLaunch";
import { kycTierNumberToLabel } from "@/lib/trustlayerLaunchContext";
import { Loader2, Shield } from "lucide-react";

const scopeColors: Record<string, string> = {
  openid: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
  profile: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-200",
  email: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200",
  kyc_status: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
  trust_score: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200",
};

function ScopeTag({ scope }: { scope: string }) {
  const cls = scopeColors[scope] || "bg-muted text-muted-foreground";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {scope}
    </span>
  );
}

type Props = {
  app: AppResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function MarketplaceAppConsentDialog({ app, open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const { toast } = useToast();
  const hasOrigin = Boolean(deriveAppOrigin(app));

  const { data: me, isLoading: loadingMe } = useQuery({
    queryKey: ["identity-me"],
    queryFn: () => authApi.me(),
    enabled: open,
  });

  const { data: trust, isLoading: loadingTrust } = useQuery({
    queryKey: ["trust-profile"],
    queryFn: () => trustApi.getProfile(),
    enabled: open,
  });

  const loadingPreview = open && (loadingMe || loadingTrust);

  const grantMutation = useMutation({
    mutationFn: () => consentApi.grant(app.client_id, app.allowed_scopes ?? []),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["consents-mine"] });
      await qc.invalidateQueries({ queryKey: ["apps-marketplace"] });
      const url = await openLaunchDashboardInNewTab(app);
      toast({
        title: "Access granted",
        description: url ? "Opening the app in a new tab." : "Consent saved. Add a redirect URI to the app to open it automatically.",
      });
      onOpenChange(false);
    },
    onError: (e: Error) =>
      toast({ title: "Could not save consent", description: e.message, variant: "destructive" }),
  });

  const scopes = app.allowed_scopes ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Allow {app.name}?
          </DialogTitle>
          <DialogDescription>
            This app is requesting access to the following TrustLayer data. Only continue if you trust this app.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Requested access</p>
            {scopes.length === 0 ? (
              <p className="text-muted-foreground text-xs">No scopes listed for this app.</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {scopes.map((s) => (
                  <ScopeTag key={s} scope={s} />
                ))}
              </div>
            )}
          </div>

          <div className="rounded-lg border bg-muted/30 p-3 space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Shared on launch</p>
            {loadingPreview ? (
              <div className="flex items-center gap-2 text-muted-foreground py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading your profile…
              </div>
            ) : me && trust ? (
              <ul className="text-xs space-y-1">
                <li>
                  <span className="text-muted-foreground">Name:</span>{" "}
                  {me.full_name?.trim() || me.username || "—"}
                </li>
                <li>
                  <span className="text-muted-foreground">Email:</span> {me.email}
                </li>
                <li>
                  <span className="text-muted-foreground">KYC level:</span> {kycTierNumberToLabel(trust.kyc_tier)}
                </li>
                <li>
                  <span className="text-muted-foreground">Trust score:</span> {trust.trust_score}
                </li>
              </ul>
            ) : (
              <p className="text-xs text-destructive">Could not load profile preview.</p>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={grantMutation.isPending}>
            Cancel
          </Button>
          <Button
            type="button"
            disabled={grantMutation.isPending || !hasOrigin || scopes.length === 0}
            onClick={() => grantMutation.mutate()}
          >
            {grantMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving…
              </>
            ) : (
              "Allow access"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
