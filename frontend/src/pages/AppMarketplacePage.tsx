import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { appsApi, AppResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, CheckCircle2, XCircle, Shield, Globe, RefreshCcw, Copy, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/shared/PageHeader";
import UserAppsHub from "./UserAppsHub";
import { MarketplaceAppCard } from "@/components/apps/MarketplaceAppCard";

const scopeColors: Record<string, string> = {
  openid: "bg-blue-100 text-blue-800",
  profile: "bg-purple-100 text-purple-800",
  email: "bg-green-100 text-green-800",
  kyc_status: "bg-amber-100 text-amber-800",
  trust_score: "bg-orange-100 text-orange-800",
  transaction_history: "bg-red-100 text-red-800",
};

function ScopeTag({ scope }: { scope: string }) {
  const cls = scopeColors[scope] || "bg-muted text-muted-foreground";
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{scope}</span>;
}

function AppCard({ app, onApprove, onDeactivate }: {
  app: AppResponse;
  /** Admin: approve pending apps */
  onApprove?: (id: string) => void;
  /** Admin (any) or app owner (own apps only, enforced by API) */
  onDeactivate?: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const copyId = () => {
    navigator.clipboard.writeText(app.client_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <Card className="flex flex-col hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{app.name}</CardTitle>
            <CardDescription className="mt-0.5 line-clamp-2">{app.description || "No description"}</CardDescription>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <Badge variant={app.is_approved ? "default" : "secondary"} className="text-xs">
              {app.is_approved ? "Approved" : "Pending"}
            </Badge>
            <Badge variant={app.is_active ? "outline" : "destructive"} className="text-xs">
              {app.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Globe className="h-3.5 w-3.5 shrink-0" />
          <code className="truncate max-w-[180px]">{app.client_id}</code>
          <button onClick={copyId} className="hover:text-foreground transition-colors">
            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
          </button>
        </div>
        {app.allowed_scopes?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {app.allowed_scopes.slice(0, 4).map(s => <ScopeTag key={s} scope={s} />)}
            {app.allowed_scopes.length > 4 && (
              <span className="text-xs text-muted-foreground">+{app.allowed_scopes.length - 4}</span>
            )}
          </div>
        )}
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
      </CardContent>
    </Card>
  );
}

export default function AppMarketplacePage() {
  const { role } = useAuth();
  if (role === "user") {
    return <UserAppsHub />;
  }

  const isAdmin = role === "admin";
  const isAppOwner = role === "app_owner";
  const canRegisterApp = isAdmin || isAppOwner;
  const defaultTab = isAdmin ? "all" : "mine";
  const qc = useQueryClient();
  const { toast } = useToast();

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scopes, setScopes] = useState("openid profile email");
  const [redirectUris, setRedirectUris] = useState("http://localhost:3000/callback");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newAppSecret, setNewAppSecret] = useState<{ client_id: string; client_secret: string } | null>(null);

  const { data: allApps = [], isLoading: loadingAll } = useQuery({
    queryKey: ["apps-all"],
    queryFn: () => appsApi.list(),
    enabled: isAdmin,
  });

  const { data: myApps = [], isLoading: loadingMine } = useQuery({
    queryKey: ["apps-mine"],
    queryFn: () => appsApi.mine(),
  });

  const { data: marketplace = [], isLoading: loadingMarket } = useQuery({
    queryKey: ["apps-marketplace"],
    queryFn: () => appsApi.marketplace(),
  });

  const registerMutation = useMutation({
    mutationFn: () => appsApi.register({
      name,
      description,
      allowed_scopes: scopes.split(/[\s,]+/).filter(Boolean),
      redirect_uris: redirectUris.split(/[\s,]+/).filter(Boolean),
    }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["apps-mine"] });
      if (isAdmin) qc.invalidateQueries({ queryKey: ["apps-all"] });
      setDialogOpen(false);
      if (data.client_secret) {
        setNewAppSecret({ client_id: data.client_id, client_secret: data.client_secret });
      }
      setName(""); setDescription(""); setScopes("openid profile email");
      toast({ title: "App registered", description: "Your app is pending approval." });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => appsApi.approve(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["apps-all"] });
      qc.invalidateQueries({ queryKey: ["apps-mine"] });
      qc.invalidateQueries({ queryKey: ["apps-marketplace"] });
      toast({ title: "App approved" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => appsApi.deactivate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["apps-all"] });
      qc.invalidateQueries({ queryKey: ["apps-mine"] });
      qc.invalidateQueries({ queryKey: ["apps-marketplace"] });
      toast({ title: "App deactivated" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="App directory"
        description={
          isAdmin
            ? "All OAuth clients: pending approval and approved. You can approve or deactivate any application."
            : "Register OAuth2 clients and manage only your own applications (My Apps). Browse approved public listings in Marketplace."
        }
      >
        {canRegisterApp && (
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" /> Register app
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Register a New App</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">App Name *</label>
                <Input value={name} onChange={e => setName(e.target.value)} placeholder="My Finance App" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Description</label>
                <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="Short description…" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Allowed Scopes (space-separated)</label>
                <Input value={scopes} onChange={e => setScopes(e.target.value)} placeholder="openid profile email kyc_status" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Redirect URIs (space-separated)</label>
                <Input value={redirectUris} onChange={e => setRedirectUris(e.target.value)} placeholder="https://myapp.com/callback" />
              </div>
              <Button
                className="w-full"
                disabled={!name || registerMutation.isPending}
                onClick={() => registerMutation.mutate()}
              >
                {registerMutation.isPending ? "Registering…" : "Register App"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
        )}
      </PageHeader>

      {/* One-time secret modal */}
      {newAppSecret && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" /> App Registered — Save Your Secret
              </CardTitle>
              <CardDescription>This client secret is shown once. Copy it now.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Client ID</label>
                <code className="block bg-muted rounded p-2 text-sm break-all">{newAppSecret.client_id}</code>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Client Secret (one-time)</label>
                <code className="block bg-muted rounded p-2 text-sm break-all">{newAppSecret.client_secret}</code>
              </div>
              <Button className="w-full" onClick={() => setNewAppSecret(null)}>I've saved it</Button>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue={defaultTab}>
        <TabsList>
          {isAdmin && <TabsTrigger value="all">All Apps ({allApps.length})</TabsTrigger>}
          <TabsTrigger value="mine">My Apps ({myApps.length})</TabsTrigger>
          <TabsTrigger value="marketplace">Marketplace ({marketplace.length})</TabsTrigger>
        </TabsList>

        {isAdmin && (
          <TabsContent value="all" className="mt-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              Includes every registration: <strong>pending</strong> (awaiting approval) and <strong>approved</strong> (eligible for marketplace when public).
            </p>
            {loadingAll ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1,2,3].map(i => <Card key={i} className="h-48 animate-pulse bg-muted" />)}
              </div>
            ) : allApps.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">No apps registered yet.</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {allApps.map(app => (
                  <AppCard
                    key={app.id}
                    app={app}
                    onApprove={id => approveMutation.mutate(id)}
                    onDeactivate={id => deactivateMutation.mutate(id)}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        )}

        <TabsContent value="mine" className="mt-4">
          {loadingMine ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1,2].map(i => <Card key={i} className="h-48 animate-pulse bg-muted" />)}
            </div>
          ) : myApps.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>You haven&apos;t registered any OAuth clients yet.</p>
              {canRegisterApp && (
                <Button variant="outline" size="sm" className="mt-3" onClick={() => setDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-1" /> Register your first app
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {myApps.map(app => (
                <AppCard
                  key={app.id}
                  app={app}
                  onApprove={isAdmin ? (id) => approveMutation.mutate(id) : undefined}
                  onDeactivate={isAdmin || isAppOwner ? (id) => deactivateMutation.mutate(id) : undefined}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="marketplace" className="mt-4">
          {loadingMarket ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1,2,3].map(i => <Card key={i} className="h-48 animate-pulse bg-muted" />)}
            </div>
          ) : marketplace.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              No approved apps in the marketplace yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {marketplace.map(app => (
                <MarketplaceAppCard key={app.id} app={app} variant="user" />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
