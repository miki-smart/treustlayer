import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { mockIdentities } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
  Fingerprint, Shield, Key, Eye, EyeOff, RefreshCw, Users, CheckCircle2, XCircle,
  Lock, Download, Upload, AlertTriangle, Plus, FileText, Search, BarChart3
} from "lucide-react";

const IdentityPage = () => {
  const { role } = useAuth();
  const [selectedId, setSelectedId] = useState(mockIdentities[0]);
  const [attributes, setAttributes] = useState(selectedId.attributes);
  const [recoveryStep, setRecoveryStep] = useState<"idle" | "verify" | "reset" | "done">("idle");
  const [searchQuery, setSearchQuery] = useState("");
  const [showIssueDialog, setShowIssueDialog] = useState(false);

  const toggleShare = (key: string) => {
    setAttributes(attributes.map((a) => a.key === key ? { ...a, shared: !a.shared } : a));
  };

  const handleSelectIdentity = (id: typeof mockIdentities[0]) => {
    setSelectedId(id);
    setAttributes(id.attributes);
  };

  const startRecovery = () => {
    setRecoveryStep("verify");
    setTimeout(() => setRecoveryStep("reset"), 2000);
  };

  const completeRecovery = () => {
    setRecoveryStep("done");
    setTimeout(() => setRecoveryStep("idle"), 3000);
  };

  const filteredIdentities = mockIdentities.filter((id) =>
    id.holderName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    id.uniqueId.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (role === "user") {
    return (
      <div>
        <PageHeader title="Digital Identity" description="Manage your portable digital identity, credentials, and recovery options" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Identity Card */}
          <Card className="lg:col-span-1">
            <CardContent className="pt-6">
              <div className="text-center mb-6">
                <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                  <Fingerprint className="h-8 w-8 text-primary" />
                </div>
                <h3 className="font-semibold">{selectedId.holderName}</h3>
                <p className="text-xs font-mono text-muted-foreground mt-1">{selectedId.uniqueId}</p>
                <div className="mt-2"><StatusBadge status={selectedId.status} /></div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Created</span><span>{new Date(selectedId.createdAt).toLocaleDateString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Last Verified</span><span>{new Date(selectedId.lastVerified).toLocaleDateString()}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Credentials</span><span>{selectedId.credentials.length}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Shared Attrs</span><span>{attributes.filter(a => a.shared).length}/{attributes.length}</span></div>
              </div>
              <div className="mt-4 space-y-2">
                <Button variant="outline" size="sm" className="w-full"><RefreshCw className="mr-2 h-3 w-3" /> Re-verify Identity</Button>
                <Button variant="outline" size="sm" className="w-full"><Download className="mr-2 h-3 w-3" /> Export Identity</Button>
              </div>
            </CardContent>
          </Card>

          {/* Selective Disclosure + Vault */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="disclosure">
              <TabsList>
                <TabsTrigger value="disclosure">Selective Disclosure</TabsTrigger>
                <TabsTrigger value="vault">Identity Vault</TabsTrigger>
                <TabsTrigger value="recovery">Recovery</TabsTrigger>
              </TabsList>

              <TabsContent value="disclosure">
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground mb-4">Control which attributes are shared with requesting parties. Only shared attributes will be disclosed during verification.</p>
                    <div className="space-y-3">
                      {attributes.map((attr) => (
                        <div key={attr.key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                          <div className="flex items-center gap-3">
                            {attr.shared ? <Eye className="h-4 w-4 text-primary" /> : <EyeOff className="h-4 w-4 text-muted-foreground" />}
                            <div>
                              <p className="text-sm font-medium">{attr.key}</p>
                              <p className="text-xs text-muted-foreground">{attr.shared ? attr.value : "••••••••"}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {attr.shared && <Badge variant="secondary" className="text-[9px]">Visible</Badge>}
                            <Switch checked={attr.shared} onCheckedChange={() => toggleShare(attr.key)} />
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 p-3 bg-muted/30 rounded-lg border border-border/50">
                      <p className="text-xs text-muted-foreground">
                        <Lock className="h-3 w-3 inline mr-1" />
                        Zero-knowledge proofs allow verification without revealing actual data. Undisclosed attributes remain encrypted in your identity vault.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="vault">
                <Card>
                  <CardContent className="pt-4 space-y-4">
                    <div className="flex items-center gap-2 p-3 bg-primary/5 border border-primary/20 rounded-lg">
                      <Lock className="h-4 w-4 text-primary" />
                      <div>
                        <p className="text-sm font-medium">Identity Vault — Secured</p>
                        <p className="text-xs text-muted-foreground">AES-256 encrypted, biometric-locked storage</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {[
                        { label: "Biometric Template", type: "Encrypted", size: "2.4 KB", updated: "2026-03-25" },
                        { label: "National ID Scan", type: "Document", size: "156 KB", updated: "2026-01-15" },
                        { label: "KYC Verification Data", type: "Credential", size: "1.1 KB", updated: "2026-03-25" },
                        { label: "Voice Print", type: "Biometric", size: "4.8 KB", updated: "2026-03-20" },
                        { label: "Recovery Seed (Backup)", type: "Encrypted Key", size: "0.5 KB", updated: "2026-01-15" },
                      ].map((item) => (
                        <div key={item.label} className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-card">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center">
                              <FileText className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <div>
                              <p className="text-sm font-medium">{item.label}</p>
                              <p className="text-xs text-muted-foreground">{item.type} · {item.size}</p>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">{item.updated}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="recovery">
                <Card>
                  <CardContent className="pt-4 space-y-4">
                    <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
                      <h4 className="text-sm font-medium mb-1">Identity Recovery</h4>
                      <p className="text-xs text-muted-foreground">If you lose access to your device or biometric data, use recovery to restore your digital identity. You'll need your recovery seed phrase or trusted contact approval.</p>
                    </div>

                    {recoveryStep === "idle" && (
                      <div className="space-y-3">
                        <Button onClick={startRecovery} className="w-full"><Key className="mr-2 h-4 w-4" /> Start Recovery Process</Button>
                        <Button variant="outline" className="w-full"><Users className="mr-2 h-4 w-4" /> Request Social Recovery</Button>
                        <div className="grid grid-cols-2 gap-3">
                          <Button variant="outline" size="sm"><Download className="mr-2 h-3 w-3" /> Backup Seed</Button>
                          <Button variant="outline" size="sm"><Upload className="mr-2 h-3 w-3" /> Import Seed</Button>
                        </div>
                      </div>
                    )}

                    {recoveryStep === "verify" && (
                      <div className="text-center py-6">
                        <div className="h-12 w-12 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-3" />
                        <p className="text-sm font-medium">Verifying recovery credentials...</p>
                        <p className="text-xs text-muted-foreground mt-1">Checking biometric backup and seed phrase</p>
                      </div>
                    )}

                    {recoveryStep === "reset" && (
                      <div className="space-y-3">
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                          <p className="text-sm text-amber-700"><AlertTriangle className="h-4 w-4 inline mr-1" /> Identity recovery requires re-verification</p>
                        </div>
                        <Input placeholder="Enter your 24-word recovery phrase" />
                        <Button onClick={completeRecovery} className="w-full">Complete Recovery</Button>
                      </div>
                    )}

                    {recoveryStep === "done" && (
                      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-center">
                        <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto mb-2" />
                        <p className="text-sm font-medium text-emerald-700">Identity Successfully Recovered</p>
                        <p className="text-xs text-muted-foreground mt-1">All credentials restored. New biometric enrollment required.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Credentials */}
          <Card className="lg:col-span-3">
            <CardHeader><CardTitle className="text-base">Verifiable Credentials</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {selectedId.credentials.map((cred) => (
                  <div key={cred.type} className="border rounded-lg p-4 flex items-start gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Shield className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-sm">{cred.type}</p>
                        <StatusBadge status={cred.status} />
                      </div>
                      <p className="text-xs text-muted-foreground">Issued by {cred.issuer}</p>
                      <p className="text-xs text-muted-foreground">Expires: {cred.expiresAt}</p>
                      <div className="flex gap-2 mt-2">
                        <Button variant="ghost" size="sm" className="text-xs h-7"><Eye className="mr-1 h-3 w-3" /> View Proof</Button>
                        <Button variant="ghost" size="sm" className="text-xs h-7"><Download className="mr-1 h-3 w-3" /> Export</Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Admin view
  return (
    <div>
      <PageHeader title="Identity Management" description="Identity lifecycle management, credential issuance, and analytics">
        <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
          <DialogTrigger asChild>
            <Button size="sm"><Plus className="mr-2 h-4 w-4" /> Issue Credential</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Issue New Credential</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Holder</label>
                <Input placeholder="Search identity holder..." />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Credential Type</label>
                <Input placeholder="e.g. KYC Verified, Bank Account" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Issuing Organization</label>
                <Input placeholder="e.g. FinInfra Platform" />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Expiry Date</label>
                <Input type="date" />
              </div>
              <Button className="w-full" onClick={() => setShowIssueDialog(false)}>Issue Credential</Button>
            </div>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard title="Total Identities" value={mockIdentities.length} icon={Fingerprint} />
        <StatCard title="Active" value={mockIdentities.filter((i) => i.status === "active").length} icon={CheckCircle2} />
        <StatCard title="Suspended" value={mockIdentities.filter((i) => i.status === "suspended").length} icon={XCircle} iconColor="bg-amber-500" />
        <StatCard title="Total Credentials" value={mockIdentities.reduce((acc, id) => acc + id.credentials.length, 0)} icon={Shield} />
      </div>

      <Tabs defaultValue="lifecycle">
        <TabsList>
          <TabsTrigger value="lifecycle">Identity Lifecycle</TabsTrigger>
          <TabsTrigger value="credentials">All Credentials</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="lifecycle">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Identity Lifecycle</CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search identities..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9 h-9" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Holder</TableHead>
                    <TableHead>Unique ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Credentials</TableHead>
                    <TableHead>Attributes</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Verified</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredIdentities.map((id) => (
                    <TableRow key={id.id}>
                      <TableCell className="font-medium text-sm">{id.holderName}</TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">{id.uniqueId}</TableCell>
                      <TableCell><StatusBadge status={id.status} /></TableCell>
                      <TableCell className="text-sm">{id.credentials.length} credential(s)</TableCell>
                      <TableCell className="text-sm">{id.attributes.length} ({id.attributes.filter(a => a.shared).length} shared)</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{new Date(id.createdAt).toLocaleDateString()}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{new Date(id.lastVerified).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" className="text-xs">View</Button>
                          <Button variant="ghost" size="sm" className="text-xs">Suspend</Button>
                          <Button variant="ghost" size="sm" className="text-xs text-destructive">Revoke</Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="credentials">
          <Card>
            <CardHeader><CardTitle className="text-base">All Issued Credentials</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Holder</TableHead>
                    <TableHead>Credential Type</TableHead>
                    <TableHead>Issuer</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockIdentities.flatMap((id) =>
                    id.credentials.map((cred) => (
                      <TableRow key={`${id.id}-${cred.type}`}>
                        <TableCell className="font-medium text-sm">{id.holderName}</TableCell>
                        <TableCell className="text-sm">{cred.type}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{cred.issuer}</TableCell>
                        <TableCell><StatusBadge status={cred.status} /></TableCell>
                        <TableCell className="text-sm text-muted-foreground">{cred.expiresAt}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="sm" className="text-xs">Renew</Button>
                            <Button variant="ghost" size="sm" className="text-xs text-destructive">Revoke</Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle className="text-base flex items-center gap-2"><BarChart3 className="h-4 w-4" /> Identity Status Distribution</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: "Active", count: mockIdentities.filter(i => i.status === "active").length, total: mockIdentities.length, color: "bg-emerald-500" },
                  { label: "Suspended", count: mockIdentities.filter(i => i.status === "suspended").length, total: mockIdentities.length, color: "bg-amber-500" },
                  { label: "Revoked", count: mockIdentities.filter(i => i.status === "revoked").length, total: mockIdentities.length, color: "bg-destructive" },
                  { label: "Pending", count: mockIdentities.filter(i => i.status === "pending").length, total: mockIdentities.length, color: "bg-muted-foreground" },
                ].map(({ label, count, total, color }) => (
                  <div key={label} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{label}</span>
                      <span className="font-medium">{count} ({total > 0 ? Math.round((count / total) * 100) : 0}%)</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${color}`} style={{ width: `${total > 0 ? (count / total) * 100 : 0}%` }} />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-base">Credential Issuance Summary</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {["National ID", "KYC Verified", "Passport", "Bank Account Verified"].map((type) => {
                  const count = mockIdentities.flatMap(i => i.credentials).filter(c => c.type === type).length;
                  return (
                    <div key={type} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-primary" />
                        <span className="text-sm">{type}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">{count} issued</Badge>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default IdentityPage;
