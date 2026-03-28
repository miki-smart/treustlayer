import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { consentApi, appsApi, sessionApi, type AppResponse, type ConsentResponse, type ActiveSessionResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Link2, ShieldCheck, ExternalLink, MonitorSmartphone, Globe, LogOut, ShieldOff, Rocket,
} from "lucide-react";
import { openLaunchDashboardInNewTab } from "@/lib/launchDownstreamDashboard";
import { useToast } from "@/hooks/use-toast";

function buildClientLookup(apps: AppResponse[]): Map<string, AppResponse> {
  const m = new Map<string, AppResponse>();
  for (const a of apps) m.set(a.client_id, a);
  return m;
}

/**
 * End-user view: connected OAuth apps with revoke access + per-session revoke.
 * No separate consent page — actions live here.
 */
export function UserConnectionsPanel() {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [launchingId, setLaunchingId] = useState<string | null>(null);

  const { data: consents = [], isLoading: loadingConsents } = useQuery({
    queryKey: ["consents-mine"],
    queryFn: () => consentApi.listMine(),
  });

  const { data: marketplace = [], isLoading: loadingMarket } = useQuery({
    queryKey: ["apps-marketplace"],
    queryFn: () => appsApi.marketplace(),
  });

  const { data: sessions = [], isLoading: loadingSessions } = useQuery({
    queryKey: ["sessions-active"],
    queryFn: () => sessionApi.listActive(),
  });

  const lookup = useMemo(() => buildClientLookup(marketplace), [marketplace]);

  const sessionsByClient = useMemo(() => {
    const m = new Map<string, ActiveSessionResponse[]>();
    for (const s of sessions) {
      const list = m.get(s.client_id) ?? [];
      list.push(s);
      m.set(s.client_id, list);
    }
    return m;
  }, [sessions]);

  const activeConsents = useMemo(
    () => consents.filter((c) => c.is_active),
    [consents],
  );

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["consents-mine"] });
    qc.invalidateQueries({ queryKey: ["sessions-active"] });
  };

  const revokeAccessMutation = useMutation({
    mutationFn: (client_id: string) => consentApi.revoke(client_id),
    onSuccess: () => {
      invalidate();
      toast({ title: "Access revoked", description: "This app can no longer use your data until you authorize it again." });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const revokeSessionMutation = useMutation({
    mutationFn: (token_id: string) => sessionApi.revoke(token_id),
    onSuccess: () => {
      invalidate();
      toast({ title: "Session ended" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const handleLaunch = async (meta: AppResponse | undefined, client_id: string) => {
    if (!meta) {
      toast({ title: "Cannot launch", description: "App metadata not found in marketplace.", variant: "destructive" });
      return;
    }
    setLaunchingId(client_id);
    try {
      const url = await openLaunchDashboardInNewTab(meta);
      if (!url) toast({ title: "Cannot launch", description: "Missing redirect URI for this app.", variant: "destructive" });
    } catch (e) {
      toast({ title: "Launch failed", description: e instanceof Error ? e.message : "Unknown error", variant: "destructive" });
    } finally {
      setLaunchingId(null);
    }
  };

  const revokeAllSessionsMutation = useMutation({
    mutationFn: async (client_id: string) => {
      const list = await sessionApi.listActive();
      const forClient = list.filter((s) => s.client_id === client_id);
      await Promise.all(forClient.map((s) => sessionApi.revoke(s.id)));
      return forClient.length;
    },
    onSuccess: (n) => {
      invalidate();
      toast({ title: "Sessions revoked", description: `Signed out ${n} active session(s) for this app.` });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const loading = loadingConsents || loadingMarket || loadingSessions;

  if (loading) {
    return (
      <div className="grid gap-4">
        {[1, 2].map((i) => (
          <Card key={i} className="h-40 animate-pulse bg-muted/60" />
        ))}
      </div>
    );
  }

  if (activeConsents.length === 0) {
    return (
      <Card>
        <CardContent className="py-14 text-center space-y-4">
          <Link2 className="h-12 w-12 mx-auto text-muted-foreground/40" />
          <div>
            <p className="font-medium">No connected apps yet</p>
            <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
              When you sign in to a third-party app with TrustLayer, it will appear here. Browse the Marketplace tab to see approved apps.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4">
      {activeConsents.map((c: ConsentResponse) => {
        const meta = lookup.get(c.client_id);
        const sess = sessionsByClient.get(c.client_id) ?? [];
        return (
          <Card key={c.id} className="overflow-hidden">
            <CardHeader className="pb-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1 min-w-0">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Link2 className="h-5 w-5 shrink-0 text-primary" />
                    <span className="truncate">{meta?.name ?? c.client_id}</span>
                  </CardTitle>
                  <CardDescription className="line-clamp-2">
                    {meta?.description || "OAuth client you've authorized with TrustLayer."}
                  </CardDescription>
                </div>
                <div className="flex flex-wrap gap-2 shrink-0">
                  {meta?.category && <Badge variant="secondary">{meta.category}</Badge>}
                  <Badge variant="default" className="gap-1">
                    <ShieldCheck className="h-3 w-3" />
                    Connected
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Client ID</p>
                <code className="block bg-muted/80 rounded-md px-3 py-2 text-xs font-mono break-all">{c.client_id}</code>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Granted access (scopes)</p>
                <div className="flex flex-wrap gap-1.5">
                  {c.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="inline-flex items-center rounded-full bg-primary/10 text-primary px-2.5 py-0.5 text-xs font-medium"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              </div>

              {meta && meta.redirect_uris?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1.5">
                    <Globe className="h-3.5 w-3.5" />
                    Registered redirect URIs
                  </p>
                  <ul className="space-y-1">
                    {meta.redirect_uris.map((uri, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs font-mono text-muted-foreground">
                        <ExternalLink className="h-3 w-3 mt-0.5 shrink-0" />
                        <span className="break-all">{uri}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="rounded-lg border bg-muted/30 p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium flex items-center gap-1.5">
                    <MonitorSmartphone className="h-4 w-4" />
                    Active sessions ({sess.length})
                  </p>
                  {sess.length > 0 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs"
                      disabled={revokeAllSessionsMutation.isPending || revokeSessionMutation.isPending}
                      onClick={() => revokeAllSessionsMutation.mutate(c.client_id)}
                    >
                      <LogOut className="h-3 w-3 mr-1" />
                      Revoke all sessions
                    </Button>
                  )}
                </div>
                {sess.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No active refresh-token sessions for this app.</p>
                ) : (
                  <ul className="space-y-2">
                    {sess.map((s) => (
                      <li
                        key={s.id}
                        className="flex flex-wrap items-center justify-between gap-2 text-xs border rounded-md px-2 py-1.5 bg-background"
                      >
                        <span className="text-muted-foreground font-mono truncate max-w-[200px]">{s.id.slice(0, 8)}…</span>
                        <span className="text-muted-foreground">{s.device_info || "Device"}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs shrink-0"
                          disabled={revokeSessionMutation.isPending}
                          onClick={() => revokeSessionMutation.mutate(s.id)}
                        >
                          Revoke session
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="flex flex-wrap justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="default"
                  size="sm"
                  className="gap-1.5"
                  disabled={launchingId === c.client_id || !meta}
                  title={meta ? "Open app dashboard with your TrustLayer context" : "App not in marketplace list"}
                  onClick={() => handleLaunch(meta, c.client_id)}
                >
                  <Rocket className="h-4 w-4" />
                  {launchingId === c.client_id ? "Opening…" : "Launch app"}
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  className="gap-1.5"
                  disabled={revokeAccessMutation.isPending}
                  onClick={() => {
                    if (window.confirm(`Revoke all access for ${meta?.name ?? c.client_id}? This removes consent and you must sign in again to use this app.`)) {
                      revokeAccessMutation.mutate(c.client_id);
                    }
                  }}
                >
                  <ShieldOff className="h-4 w-4" />
                  Revoke app access
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
