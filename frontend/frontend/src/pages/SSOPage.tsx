import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { mockSSOProviders, mockSSOSessions, mockConsents } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KeyRound, Globe, Users, Monitor, Trash2, Shield, Link2, Unlink } from "lucide-react";

const SSOPage = () => {
  const { role } = useAuth();
  const [consents, setConsents] = useState(mockConsents);

  const revokeConsent = (id: string) => {
    setConsents(consents.map((c) => c.id === id ? { ...c, status: "revoked" as const } : c));
  };

  if (role === "user") {
    return (
      <div>
        <PageHeader title="SSO & Connected Apps" description="Manage your single sign-on sessions and connected applications" />

        {/* Active Sessions */}
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Monitor className="h-4 w-4" /> Active Sessions</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockSSOSessions.filter((s) => s.userId === "u2").map((session) => (
                <div key={session.id} className="flex items-center justify-between p-4 rounded-lg border border-border/60 bg-muted/20">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Globe className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{session.provider}</p>
                      <p className="text-xs text-muted-foreground">{session.device} · {session.ipAddress}</p>
                      <p className="text-xs text-muted-foreground">Login: {new Date(session.loginAt).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={session.status} />
                    {session.status === "active" && (
                      <Button variant="ghost" size="sm" className="text-destructive text-xs"><Unlink className="mr-1 h-3 w-3" /> Revoke</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Consent Management */}
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Shield className="h-4 w-4" /> App Permissions</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {consents.map((consent) => (
                <div key={consent.id} className="flex items-center justify-between p-4 rounded-lg border border-border/60 bg-muted/20">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{consent.appName}</p>
                      <StatusBadge status={consent.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">via {consent.provider}</p>
                    <div className="flex gap-1 mt-2">
                      {consent.scopesGranted.map((scope) => (
                        <Badge key={scope} variant="secondary" className="text-[10px]">{scope}</Badge>
                      ))}
                    </div>
                  </div>
                  {consent.status === "active" && (
                    <Button variant="ghost" size="sm" className="text-destructive text-xs" onClick={() => revokeConsent(consent.id)}>
                      <Trash2 className="mr-1 h-3 w-3" /> Revoke
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Admin
  return (
    <div>
      <PageHeader title="SSO Federation" description="Manage federated authentication and connected institutions">
        <Button size="sm"><Link2 className="mr-2 h-4 w-4" /> Add Provider</Button>
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard title="Connected Providers" value={mockSSOProviders.filter((p) => p.status === "active").length} icon={KeyRound} />
        <StatCard title="Active Sessions" value={mockSSOSessions.filter((s) => s.status === "active").length} icon={Monitor} />
        <StatCard title="Total SSO Users" value={mockSSOProviders.reduce((sum, p) => sum + p.usersCount, 0)} icon={Users} />
        <StatCard title="Regions" value="2" icon={Globe} />
      </div>

      {/* Federation table */}
      <Card className="mb-6">
        <CardHeader><CardTitle className="text-base">Connected Institutions</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Institution</TableHead>
                <TableHead>Protocol</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Users</TableHead>
                <TableHead>Region</TableHead>
                <TableHead>Last Sync</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockSSOProviders.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium text-sm">{p.name}</TableCell>
                  <TableCell><Badge variant="secondary" className="text-xs">{p.protocol}</Badge></TableCell>
                  <TableCell><StatusBadge status={p.status} /></TableCell>
                  <TableCell className="text-sm">{p.usersCount.toLocaleString()}</TableCell>
                  <TableCell className="text-sm">{p.region}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{p.lastSync ? new Date(p.lastSync).toLocaleString() : "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Session Monitor */}
      <Card>
        <CardHeader><CardTitle className="text-base">Session Monitor</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Device</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Expires</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockSSOSessions.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium text-sm">{s.userName}</TableCell>
                  <TableCell className="text-sm">{s.provider}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{s.device}</TableCell>
                  <TableCell className="text-sm font-mono text-muted-foreground">{s.ipAddress}</TableCell>
                  <TableCell><StatusBadge status={s.status} /></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{new Date(s.expiresAt).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default SSOPage;
