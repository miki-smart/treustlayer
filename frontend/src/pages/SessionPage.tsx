import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { sessionApi, webhooksApi, appsApi, type ActiveSessionResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { MonitorSmartphone, LogOut, RotateCcw, Webhook, CheckCircle2, XCircle, Clock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/shared/PageHeader";

function SessionCard({ session, onRevoke }: { session: ActiveSessionResponse; onRevoke: () => void }) {
  const expires = new Date(session.expires_at);
  const isExpired = expires < new Date();
  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <MonitorSmartphone className="h-4 w-4 text-muted-foreground shrink-0" />
            <div>
              <CardTitle className="text-sm font-medium">{session.client_id}</CardTitle>
              <CardDescription className="text-xs">
                Created: {new Date(session.created_at).toLocaleString()}
              </CardDescription>
            </div>
          </div>
          <Badge variant={isExpired ? "secondary" : "default"} className="text-xs shrink-0">
            {isExpired ? "Expired" : "Active"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1">
          {session.scopes.map((s) => (
            <span key={s} className="inline-flex rounded-full bg-muted text-muted-foreground px-2 py-0.5 text-xs">
              {s}
            </span>
          ))}
        </div>
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="h-3 w-3" />
          Expires: {expires.toLocaleString()}
        </p>
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs text-destructive hover:bg-destructive/10 border-destructive/30"
          onClick={onRevoke}
        >
          <LogOut className="h-3 w-3 mr-1" /> Revoke
        </Button>
      </CardContent>
    </Card>
  );
}

function DeliveryBadge({ status }: { status: string }) {
  if (status === "delivered" || status === "success")
    return (
      <Badge className="bg-green-100 text-green-800 text-xs">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        Delivered
      </Badge>
    );
  if (status === "failed")
    return (
      <Badge variant="destructive" className="text-xs">
        <XCircle className="h-3 w-3 mr-1" />
        Failed
      </Badge>
    );
  return (
    <Badge variant="secondary" className="text-xs">
      <Clock className="h-3 w-3 mr-1" />
      Pending
    </Badge>
  );
}

export default function SessionPage() {
  const { role } = useAuth();
  const isAdmin = role === "admin";
  const qc = useQueryClient();
  const { toast } = useToast();

  const [webhookClientId, setWebhookClientId] = useState("");
  const [deliverySubId, setDeliverySubId] = useState("");

  const { data: sessions = [], isLoading: loadingSessions } = useQuery({
    queryKey: ["sessions-active"],
    queryFn: () => sessionApi.listActive(),
  });

  const { data: adminApps = [] } = useQuery({
    queryKey: ["admin-apps-webhooks"],
    queryFn: () => appsApi.list(0, 200),
    enabled: isAdmin,
  });

  useEffect(() => {
    if (!isAdmin || !adminApps.length || webhookClientId) return;
    setWebhookClientId(adminApps[0].client_id);
  }, [isAdmin, adminApps, webhookClientId]);

  const { data: subscriptions = [], isLoading: loadingSubs } = useQuery({
    queryKey: ["webhook-subs", webhookClientId],
    queryFn: () => webhooksApi.listSubscriptions(webhookClientId),
    enabled: isAdmin && !!webhookClientId,
  });

  useEffect(() => {
    if (!subscriptions.length) {
      setDeliverySubId("");
      return;
    }
    setDeliverySubId((prev) => (prev && subscriptions.some((s) => s.id === prev) ? prev : subscriptions[0].id));
  }, [subscriptions]);

  const { data: deliveries = [], isLoading: loadingDel } = useQuery({
    queryKey: ["webhook-del", deliverySubId],
    queryFn: () => webhooksApi.listDeliveries(deliverySubId),
    enabled: isAdmin && !!deliverySubId,
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => sessionApi.revoke(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions-active"] });
      toast({ title: "Session revoked" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const revokeAllMutation = useMutation({
    mutationFn: () => sessionApi.revokeAll(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions-active"] });
      toast({ title: "All sessions revoked" });
    },
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.retry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["webhook-del", deliverySubId] });
      toast({ title: "Retry queued" });
    },
  });

  const deactivateSubMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.deactivate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["webhook-subs", webhookClientId] });
      toast({ title: "Subscription deactivated" });
    },
  });

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Sessions & Webhooks"
        description="Manage your active sessions and webhook event subscriptions."
      />

      <Tabs defaultValue="sessions">
        <TabsList>
          <TabsTrigger value="sessions">Active Sessions ({sessions.length})</TabsTrigger>
          {isAdmin && <TabsTrigger value="webhooks">Webhooks ({subscriptions.length})</TabsTrigger>}
          {isAdmin && <TabsTrigger value="deliveries">Deliveries ({deliveries.length})</TabsTrigger>}
        </TabsList>

        <TabsContent value="sessions" className="mt-4 space-y-4">
          {sessions.length > 0 && (
            <div className="flex justify-end">
              <Button
                size="sm"
                variant="destructive"
                className="gap-1.5"
                disabled={revokeAllMutation.isPending}
                onClick={() => revokeAllMutation.mutate()}
              >
                <RotateCcw className="h-4 w-4" /> Revoke All Sessions
              </Button>
            </div>
          )}
          {loadingSessions ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2].map((i) => (
                <Card key={i} className="h-40 animate-pulse bg-muted" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <MonitorSmartphone className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>No active sessions found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessions.map((s) => (
                <SessionCard key={s.id} session={s} onRevoke={() => revokeMutation.mutate(s.id)} />
              ))}
            </div>
          )}
        </TabsContent>

        {isAdmin && (
          <TabsContent value="webhooks" className="mt-4 space-y-4">
            <div className="space-y-2 max-w-md">
              <Label>OAuth client (app)</Label>
              <Select
                value={webhookClientId || undefined}
                onValueChange={(v) => {
                  setWebhookClientId(v);
                  setDeliverySubId("");
                }}
                disabled={!adminApps.length}
              >
                <SelectTrigger>
                  <SelectValue placeholder={adminApps.length ? "Select app" : "No apps in registry"} />
                </SelectTrigger>
                <SelectContent>
                  {adminApps.map((a) => (
                    <SelectItem key={a.client_id} value={a.client_id}>
                      {a.name} ({a.client_id})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Subscriptions are listed per client_id, matching the API.
              </p>
            </div>
            {loadingSubs ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[1, 2].map((i) => (
                  <Card key={i} className="h-36 animate-pulse bg-muted" />
                ))}
              </div>
            ) : !webhookClientId ? (
              <div className="text-center py-12 text-muted-foreground text-sm">Select an app to load subscriptions.</div>
            ) : subscriptions.length === 0 ? (
              <div className="text-center py-20 text-muted-foreground">
                <Webhook className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No webhook subscriptions for this client.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {subscriptions.map((sub) => (
                  <Card key={sub.id} className="hover:shadow-sm transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <CardTitle className="text-sm font-medium">{sub.event_type}</CardTitle>
                          <CardDescription className="text-xs">
                            {sub.client_id} · {new Date(sub.created_at).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <Badge variant={sub.is_active ? "default" : "secondary"} className="text-xs shrink-0">
                          {sub.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <p className="text-xs text-muted-foreground break-all">{sub.target_url}</p>
                      {sub.is_active && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs text-destructive hover:bg-destructive/10 border-destructive/30"
                          onClick={() => deactivateSubMutation.mutate(sub.id)}
                        >
                          <XCircle className="h-3 w-3 mr-1" /> Deactivate
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        )}

        {isAdmin && (
          <TabsContent value="deliveries" className="mt-4 space-y-4">
            <div className="space-y-2 max-w-md">
              <Label>Subscription</Label>
              <Select
                value={deliverySubId || undefined}
                onValueChange={setDeliverySubId}
                disabled={!subscriptions.length}
              >
                <SelectTrigger>
                  <SelectValue placeholder={subscriptions.length ? "Select subscription" : "No subscriptions"} />
                </SelectTrigger>
                <SelectContent>
                  {subscriptions.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.event_type} — {s.id.slice(0, 8)}…
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {loadingDel ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="h-20 animate-pulse bg-muted" />
                ))}
              </div>
            ) : !deliverySubId ? (
              <div className="text-center py-12 text-muted-foreground text-sm">
                Choose a subscription to load deliveries.
              </div>
            ) : deliveries.length === 0 ? (
              <div className="text-center py-20 text-muted-foreground">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No deliveries for this subscription.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {deliveries.map((d) => (
                  <Card key={d.id} className="p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <DeliveryBadge status={d.status} />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{d.event_type}</p>
                          <p className="text-xs text-muted-foreground truncate">{d.target_url}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-muted-foreground">{d.attempts} attempts</span>
                        {d.status === "failed" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => retryMutation.mutate(d.id)}
                          >
                            <RotateCcw className="h-3 w-3 mr-1" /> Retry
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
