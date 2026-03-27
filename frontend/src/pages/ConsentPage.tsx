import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { consentApi, ConsentResponse } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ShieldCheck, ShieldOff, Clock, CheckCircle2, XCircle, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/shared/PageHeader";

function ConsentCard({ consent, onRevoke }: {
  consent: ConsentResponse;
  onRevoke: (client_id: string) => void;
}) {
  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {consent.is_active ? (
              <ShieldCheck className="h-5 w-5 text-green-500 shrink-0" />
            ) : (
              <ShieldOff className="h-5 w-5 text-muted-foreground shrink-0" />
            )}
            <div>
              <CardTitle className="text-sm font-semibold">{consent.client_id}</CardTitle>
              <CardDescription className="text-xs">
                Granted: {new Date(consent.granted_at).toLocaleDateString()}
              </CardDescription>
            </div>
          </div>
          <Badge variant={consent.is_active ? "default" : "secondary"} className="text-xs shrink-0">
            {consent.is_active ? "Active" : "Revoked"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {consent.scopes.map(scope => (
            <span key={scope} className="inline-flex items-center rounded-full bg-primary/10 text-primary px-2 py-0.5 text-xs font-medium">
              {scope}
            </span>
          ))}
        </div>
        {consent.revoked_at && (
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Revoked: {new Date(consent.revoked_at).toLocaleDateString()}
          </p>
        )}
        {consent.is_active && (
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs text-destructive hover:bg-destructive/10 border-destructive/30"
            onClick={() => onRevoke(consent.client_id)}
          >
            <XCircle className="h-3 w-3 mr-1" /> Revoke
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default function ConsentPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const { toast } = useToast();

  const [grantOpen, setGrantOpen] = useState(false);
  const [gClientId, setGClientId] = useState("");
  const [gScopes, setGScopes] = useState("openid profile email");

  const userId = user?.id || "";

  const { data: consents = [], isLoading } = useQuery({
    queryKey: ["consents", userId],
    queryFn: () => consentApi.listForUser(userId),
    enabled: !!userId,
  });

  const revokeMutation = useMutation({
    mutationFn: (client_id: string) => consentApi.revoke(userId, client_id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["consents", userId] });
      toast({ title: "Consent revoked" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const grantMutation = useMutation({
    mutationFn: () => consentApi.grant(userId, gClientId, gScopes.split(/[\s,]+/).filter(Boolean)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["consents", userId] });
      setGrantOpen(false);
      setGClientId(""); setGScopes("openid profile email");
      toast({ title: "Consent granted" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const active = consents.filter(c => c.is_active);
  const revoked = consents.filter(c => !c.is_active);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Consent Management"
        description="Review and manage which apps have access to your data."
      >
        <Dialog open={grantOpen} onOpenChange={setGrantOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" /> Grant Consent
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Grant Consent</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Client ID *</label>
                <Input value={gClientId} onChange={e => setGClientId(e.target.value)} placeholder="app_xxxx" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Scopes (space-separated)</label>
                <Input value={gScopes} onChange={e => setGScopes(e.target.value)} placeholder="openid profile email" />
              </div>
              <Button
                className="w-full"
                disabled={!gClientId || grantMutation.isPending}
                onClick={() => grantMutation.mutate()}
              >
                {grantMutation.isPending ? "Granting…" : "Grant"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </PageHeader>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-full bg-green-100 p-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold">{active.length}</p>
            <p className="text-xs text-muted-foreground">Active consents</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="rounded-full bg-muted p-2">
            <XCircle className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="text-2xl font-bold">{revoked.length}</p>
            <p className="text-xs text-muted-foreground">Revoked</p>
          </div>
        </Card>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3].map(i => <Card key={i} className="h-36 animate-pulse bg-muted" />)}
        </div>
      ) : consents.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <ShieldOff className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="font-medium">No consents yet</p>
          <p className="text-sm">When you connect to apps via OAuth2, consents will appear here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {active.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Active</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {active.map(c => (
                  <ConsentCard key={c.id} consent={c} onRevoke={id => revokeMutation.mutate(id)} />
                ))}
              </div>
            </div>
          )}
          {revoked.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Revoked History</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {revoked.map(c => (
                  <ConsentCard key={c.id} consent={c} onRevoke={id => revokeMutation.mutate(id)} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
