import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { StatCard } from "@/components/shared/StatCard";
import { mockCards, mockCardTransactions, mockCardRules } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
  CreditCard, ShieldCheck, Wallet, Wifi, WifiOff, RefreshCw, AlertTriangle,
  ArrowUpRight, ArrowDownLeft, Send, RotateCcw, Fingerprint, Lock, Plus,
  Smartphone, Globe, Ban, CheckCircle2, XCircle, Settings2, Eye, EyeOff
} from "lucide-react";

const txIcon: Record<string, any> = { payment: ArrowUpRight, withdrawal: ArrowDownLeft, transfer: Send, refund: RotateCcw };

const CardsPage = () => {
  const { role } = useAuth();
  const userCard = mockCards[0];
  const userTxs = mockCardTransactions.filter((t) => t.cardId === "card1");
  const userRules = mockCardRules.filter((r) => r.cardId === "card1");
  const [cvv, setCvv] = useState(userCard.dynamicCVV);
  const [rules, setRules] = useState(userRules);
  const [showCvv, setShowCvv] = useState(false);
  const [cvvTimer, setCvvTimer] = useState(30);
  const [offlineMode, setOfflineMode] = useState(false);
  const [bioBound, setBioBound] = useState(true);
  const [bioVerified, setBioVerified] = useState(false);
  const [bioVerifying, setBioVerifying] = useState(false);
  const [cardFrozen, setCardFrozen] = useState(false);
  const [walletBalance] = useState(125000);
  const [showIssueDialog, setShowIssueDialog] = useState(false);

  // Dynamic CVV rotation with countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setCvvTimer((t) => {
        if (t <= 1) {
          setCvv(String(Math.floor(100 + Math.random() * 900)));
          return 30;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleRule = (id: string) => {
    setRules(rules.map((r) => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  const simulateBioAuth = () => {
    setBioVerifying(true);
    setTimeout(() => {
      setBioVerifying(false);
      setBioVerified(true);
    }, 2500);
  };

  if (role === "user") {
    const spendPercent = (userCard.currentSpend / userCard.dailyLimit) * 100;
    const monthlyPercent = (userCard.currentSpend / userCard.monthlyLimit) * 100;

    return (
      <div>
        <PageHeader title="Card & Wallet" description="Manage your identity-linked card, wallet, and transaction controls" />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Virtual Card */}
          <Card className="lg:col-span-1">
            <CardContent className="pt-6">
              <div className={`relative rounded-2xl p-6 text-primary-foreground overflow-hidden ${cardFrozen ? "bg-muted" : "login-gradient"}`}>
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-10 -mt-10" />
                <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-8 -mb-8" />
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium uppercase ${cardFrozen ? "text-muted-foreground" : "opacity-80"}`}>{userCard.cardType} Card</span>
                      {cardFrozen && <Badge variant="destructive" className="text-[9px]">Frozen</Badge>}
                      {offlineMode && <Badge variant="secondary" className="text-[9px] gap-1"><WifiOff className="h-2.5 w-2.5" /> Offline</Badge>}
                    </div>
                    <CreditCard className={`h-6 w-6 ${cardFrozen ? "text-muted-foreground" : ""}`} />
                  </div>
                  <p className={`text-lg tracking-widest font-mono mb-4 ${cardFrozen ? "text-muted-foreground" : ""}`}>{userCard.cardNumber}</p>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-[10px] uppercase ${cardFrozen ? "text-muted-foreground" : "opacity-60"}`}>Holder</p>
                      <p className={`text-sm font-medium ${cardFrozen ? "text-muted-foreground" : ""}`}>{userCard.holderName}</p>
                    </div>
                    <div>
                      <p className={`text-[10px] uppercase ${cardFrozen ? "text-muted-foreground" : "opacity-60"}`}>Expires</p>
                      <p className={`text-sm font-medium ${cardFrozen ? "text-muted-foreground" : ""}`}>{userCard.expiresAt}</p>
                    </div>
                    <div>
                      <p className={`text-[10px] uppercase ${cardFrozen ? "text-muted-foreground" : "opacity-60"}`}>CVV</p>
                      <div className="flex items-center gap-1">
                        <p className={`text-sm font-mono font-bold ${cardFrozen ? "text-muted-foreground" : ""}`}>
                          {showCvv ? cvv : "•••"}
                        </p>
                        <button onClick={() => setShowCvv(!showCvv)} className="opacity-60 hover:opacity-100">
                          {showCvv ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* CVV Timer */}
              <div className="mt-3 flex items-center gap-2">
                <Progress value={(cvvTimer / 30) * 100} className="h-1.5 flex-1" />
                <span className="text-xs text-muted-foreground font-mono">{cvvTimer}s</span>
              </div>

              <div className="mt-4 space-y-3">
                {/* Spend limits */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Daily Spend</span>
                    <span className="font-medium">ETB {userCard.currentSpend.toLocaleString()} / {userCard.dailyLimit.toLocaleString()}</span>
                  </div>
                  <Progress value={spendPercent} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Monthly</span>
                    <span className="font-medium">ETB {userCard.currentSpend.toLocaleString()} / {userCard.monthlyLimit.toLocaleString()}</span>
                  </div>
                  <Progress value={monthlyPercent} className="h-1.5" />
                </div>

                {/* Card controls */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                    <div className="flex items-center gap-2 text-sm">
                      <Fingerprint className="h-4 w-4 text-primary" />
                      <span className="text-muted-foreground">Biometric-bound</span>
                    </div>
                    <Switch checked={bioBound} onCheckedChange={setBioBound} />
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                    <div className="flex items-center gap-2 text-sm">
                      <WifiOff className="h-4 w-4 text-amber-600" />
                      <span className="text-muted-foreground">Offline Mode</span>
                    </div>
                    <Switch checked={offlineMode} onCheckedChange={setOfflineMode} />
                  </div>
                </div>

                {/* Quick actions */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Button variant="outline" size="sm" className="text-xs"><Wallet className="mr-1 h-3 w-3" /> Wallet</Button>
                  <Button variant="outline" size="sm" className="text-xs" onClick={() => { setCvv(String(Math.floor(100 + Math.random() * 900))); setCvvTimer(30); }}>
                    <RefreshCw className="mr-1 h-3 w-3" /> New CVV
                  </Button>
                  <Button variant={cardFrozen ? "default" : "destructive"} size="sm" className="text-xs col-span-2" onClick={() => setCardFrozen(!cardFrozen)}>
                    {cardFrozen ? <><CheckCircle2 className="mr-1 h-3 w-3" /> Unfreeze Card</> : <><Ban className="mr-1 h-3 w-3" /> Freeze Card</>}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Right side — Tabs */}
          <div className="lg:col-span-2 space-y-6">
            {/* Biometric activation */}
            {bioBound && !bioVerified && (
              <Card className="border-primary/30 bg-primary/5">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Fingerprint className="h-5 w-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">Biometric Authentication Required</p>
                        <p className="text-xs text-muted-foreground">Verify your identity to enable card transactions</p>
                      </div>
                    </div>
                    <Button size="sm" onClick={simulateBioAuth} disabled={bioVerifying}>
                      {bioVerifying ? "Verifying..." : "Authenticate"}
                    </Button>
                  </div>
                  {bioVerifying && <Progress value={65} className="h-1 mt-3" />}
                </CardContent>
              </Card>
            )}

            {/* Wallet card */}
            <Card>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Wallet className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Card-Linked Wallet Balance</p>
                      <p className="text-xl font-bold text-foreground">ETB {walletBalance.toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="text-xs"><ArrowDownLeft className="mr-1 h-3 w-3" /> Top Up</Button>
                    <Button size="sm" className="text-xs"><Send className="mr-1 h-3 w-3" /> Send</Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Tabs defaultValue="transactions">
              <TabsList>
                <TabsTrigger value="transactions">Transactions</TabsTrigger>
                <TabsTrigger value="rules">Card Rules</TabsTrigger>
              </TabsList>
              <TabsContent value="transactions">
                <Card>
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      {userTxs.map((tx) => {
                        const Icon = txIcon[tx.type] || ArrowUpRight;
                        return (
                          <div key={tx.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/30 transition-colors">
                            <div className="flex items-center gap-3">
                              <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${tx.type === "refund" ? "bg-emerald-50" : "bg-muted"}`}>
                                <Icon className={`h-4 w-4 ${tx.type === "refund" ? "text-emerald-600" : "text-muted-foreground"}`} />
                              </div>
                              <div>
                                <p className="text-sm font-medium">{tx.merchant}</p>
                                <div className="flex items-center gap-2">
                                  <p className="text-xs text-muted-foreground">{new Date(tx.timestamp).toLocaleString()}</p>
                                  {tx.offline && <Badge variant="outline" className="text-[9px] gap-1"><WifiOff className="h-2.5 w-2.5" /> Offline</Badge>}
                                  {tx.status === "flagged" && <Badge variant="destructive" className="text-[9px] gap-1"><AlertTriangle className="h-2.5 w-2.5" /> Flagged</Badge>}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className={`text-sm font-medium ${tx.type === "refund" ? "text-emerald-600" : ""}`}>
                                {tx.type === "refund" ? "+" : "-"}{tx.currency} {tx.amount.toLocaleString()}
                              </p>
                              <StatusBadge status={tx.status} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="rules">
                <Card>
                  <CardContent className="pt-4 space-y-3">
                    <p className="text-sm text-muted-foreground mb-2">Programmable card rules — set risk-based spending limits and transaction controls.</p>
                    {rules.map((rule) => (
                      <div key={rule.id} className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-muted/20">
                        <div className="flex items-center gap-3">
                          <Settings2 className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-sm font-medium">{rule.ruleName}</p>
                            <p className="text-xs text-muted-foreground">{rule.condition} → {rule.action}</p>
                          </div>
                        </div>
                        <Switch checked={rule.enabled} onCheckedChange={() => toggleRule(rule.id)} />
                      </div>
                    ))}
                    <Button variant="outline" size="sm" className="w-full"><Plus className="mr-2 h-3 w-3" /> Add Custom Rule</Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    );
  }

  // Admin view
  return (
    <div>
      <PageHeader title="Card Management" description="Issue, monitor, and manage identity-linked cards, transactions, and fraud detection">
        <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
          <DialogTrigger asChild>
            <Button size="sm"><CreditCard className="mr-2 h-4 w-4" /> Issue Card</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Issue New Card</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Cardholder</label>
                <Input placeholder="Search identity holder..." />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Card Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {["Virtual", "Physical", "Biometric"].map((type) => (
                    <Button key={type} variant="outline" size="sm" className="text-xs">{type}</Button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Daily Limit (ETB)</label>
                  <Input type="number" defaultValue={50000} />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Monthly Limit (ETB)</label>
                  <Input type="number" defaultValue={500000} />
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30">
                <Fingerprint className="h-4 w-4 text-primary" />
                <span className="text-sm">Biometric-bound</span>
                <Switch className="ml-auto" defaultChecked />
              </div>
              <Button className="w-full" onClick={() => setShowIssueDialog(false)}>Issue Card</Button>
            </div>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard title="Cards Issued" value={mockCards.length} icon={CreditCard} />
        <StatCard title="Active" value={mockCards.filter((c) => c.status === "active").length} icon={ShieldCheck} />
        <StatCard title="Flagged Txns" value={mockCardTransactions.filter((t) => t.status === "flagged").length} icon={AlertTriangle} iconColor="bg-amber-500" />
        <StatCard title="Offline Txns" value={mockCardTransactions.filter((t) => t.offline).length} icon={WifiOff} />
      </div>

      <Tabs defaultValue="cards">
        <TabsList>
          <TabsTrigger value="cards">Cards</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="fraud">Fraud Detection</TabsTrigger>
          <TabsTrigger value="simulation">Transaction Sim</TabsTrigger>
        </TabsList>

        <TabsContent value="cards">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Holder</TableHead>
                    <TableHead>Card #</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Tokenized</TableHead>
                    <TableHead>Bio-bound</TableHead>
                    <TableHead>Spend</TableHead>
                    <TableHead>Issued</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockCards.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-medium text-sm">{c.holderName}</TableCell>
                      <TableCell className="font-mono text-sm">{c.cardNumber}</TableCell>
                      <TableCell><Badge variant="secondary" className="text-xs capitalize">{c.cardType}</Badge></TableCell>
                      <TableCell><StatusBadge status={c.status} /></TableCell>
                      <TableCell>{c.tokenized ? <ShieldCheck className="h-4 w-4 text-emerald-600" /> : "—"}</TableCell>
                      <TableCell>{c.biometricBound ? <Fingerprint className="h-4 w-4 text-primary" /> : "—"}</TableCell>
                      <TableCell className="text-sm">ETB {c.currentSpend.toLocaleString()}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{c.issuedAt}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transactions">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Merchant</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Offline</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockCardTransactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell className="font-medium text-sm">{tx.merchant}</TableCell>
                      <TableCell className="capitalize text-sm">{tx.type}</TableCell>
                      <TableCell className="text-sm font-medium">{tx.currency} {tx.amount.toLocaleString()}</TableCell>
                      <TableCell><StatusBadge status={tx.status} /></TableCell>
                      <TableCell className="text-sm">{tx.location}</TableCell>
                      <TableCell>{tx.offline ? <WifiOff className="h-4 w-4 text-amber-500" /> : <Wifi className="h-4 w-4 text-emerald-600" />}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{new Date(tx.timestamp).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fraud">
          <Card>
            <CardHeader><CardTitle className="text-base">Fraud Alerts</CardTitle></CardHeader>
            <CardContent>
              {mockCardTransactions.filter((t) => t.status === "flagged").map((tx) => (
                <div key={tx.id} className="border border-destructive/30 bg-destructive/5 rounded-lg p-4 mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                    <span className="text-sm font-medium text-destructive">Suspicious Transaction</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div><p className="text-muted-foreground text-xs">Merchant</p><p className="font-medium">{tx.merchant}</p></div>
                    <div><p className="text-muted-foreground text-xs">Amount</p><p className="font-medium">{tx.currency} {tx.amount.toLocaleString()}</p></div>
                    <div><p className="text-muted-foreground text-xs">Location</p><p className="font-medium">{tx.location}</p></div>
                    <div><p className="text-muted-foreground text-xs">Time</p><p className="font-medium">{new Date(tx.timestamp).toLocaleString()}</p></div>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button size="sm" variant="destructive" className="text-xs">Block Card</Button>
                    <Button size="sm" variant="outline" className="text-xs">Investigate</Button>
                    <Button size="sm" variant="outline" className="text-xs">Dismiss</Button>
                  </div>
                </div>
              ))}
              {mockCardTransactions.filter((t) => t.status === "flagged").length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-8">No fraud alerts at this time</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="simulation">
          <TransactionSimulator />
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Transaction Simulation Environment
const TransactionSimulator = () => {
  const [simResult, setSimResult] = useState<null | { status: string; message: string; riskScore: number }>(null);
  const [simulating, setSimulating] = useState(false);

  const runSimulation = () => {
    setSimulating(true);
    setSimResult(null);
    setTimeout(() => {
      const risk = Math.random();
      setSimResult({
        status: risk > 0.7 ? "flagged" : risk > 0.3 ? "completed" : "completed",
        message: risk > 0.7 ? "Transaction flagged — unusual merchant category and high amount" : "Transaction approved — within normal spending patterns",
        riskScore: Math.round(risk * 100),
      });
      setSimulating(false);
    }, 2000);
  };

  return (
    <Card>
      <CardHeader><CardTitle className="text-base">Transaction Simulation Environment</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">Test card transaction flows with configurable parameters to validate fraud detection and authorization rules.</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Amount (ETB)</label>
            <Input type="number" defaultValue={15000} />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Merchant</label>
            <Input defaultValue="Test Merchant" />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Location</label>
            <Input defaultValue="Addis Ababa" />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Type</label>
            <Input defaultValue="payment" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 p-2 rounded bg-muted/30">
            <WifiOff className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Offline</span>
            <Switch />
          </div>
          <div className="flex items-center gap-2 p-2 rounded bg-muted/30">
            <Fingerprint className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Bio-auth</span>
            <Switch defaultChecked />
          </div>
        </div>
        <Button onClick={runSimulation} disabled={simulating}>
          {simulating ? "Simulating..." : "Run Simulation"}
        </Button>

        {simResult && (
          <div className={`p-4 rounded-lg border ${simResult.status === "flagged" ? "border-destructive/30 bg-destructive/5" : "border-emerald-200 bg-emerald-50"}`}>
            <div className="flex items-center gap-2 mb-2">
              {simResult.status === "flagged" ? <AlertTriangle className="h-4 w-4 text-destructive" /> : <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
              <span className={`text-sm font-medium ${simResult.status === "flagged" ? "text-destructive" : "text-emerald-700"}`}>
                {simResult.status === "flagged" ? "Transaction Flagged" : "Transaction Approved"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{simResult.message}</p>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Risk Score:</span>
              <Progress value={simResult.riskScore} className="h-2 w-32" />
              <span className="text-xs font-medium">{simResult.riskScore}%</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CardsPage;
