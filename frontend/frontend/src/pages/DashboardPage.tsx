import { useAuth } from "@/contexts/AuthContext";
import { StatCard } from "@/components/shared/StatCard";
import { PageHeader } from "@/components/shared/PageHeader";
import { dashboardStats, monthlyData, mockAuditLog } from "@/data/mockData";
import { Users, Fingerprint, FileCheck, CreditCard, Activity, ShieldAlert, KeyRound, ScanFace } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area } from "recharts";

const DashboardPage = () => {
  const { role } = useAuth();

  const stats = [
    { title: "Total Users", value: dashboardStats.totalUsers, change: "+6.4% from last month", changeType: "positive" as const, icon: Users },
    { title: "Active Identities", value: dashboardStats.activeIdentities, change: "+3.2%", changeType: "positive" as const, icon: Fingerprint },
    { title: "KYC Completed", value: dashboardStats.kycCompleted, change: "+2.1%", changeType: "positive" as const, icon: FileCheck },
    { title: "Cards Issued", value: dashboardStats.cardIssued, change: "+8.7%", changeType: "positive" as const, icon: CreditCard },
  ];

  const adminStats = [
    { title: "Transactions Today", value: dashboardStats.transactionsToday, change: "+12.3%", changeType: "positive" as const, icon: Activity },
    { title: "Fraud Blocked", value: dashboardStats.fraudBlocked, change: "-15% from avg", changeType: "positive" as const, icon: ShieldAlert, iconColor: "bg-destructive" },
    { title: "SSO Logins", value: dashboardStats.ssoLogins, change: "+5.8%", changeType: "positive" as const, icon: KeyRound },
    { title: "Biometric Verifications", value: dashboardStats.biometricVerifications, change: "+9.1%", changeType: "positive" as const, icon: ScanFace },
  ];

  return (
    <div>
      <PageHeader
        title={role === "admin" ? "Admin Dashboard" : "My Dashboard"}
        description={role === "admin" ? "Infrastructure overview and system health" : "Your identity and financial services overview"}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {stats.map((s) => <StatCard key={s.title} {...s} />)}
      </div>

      {role === "admin" && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          {adminStats.map((s) => <StatCard key={s.title} {...s} />)}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader><CardTitle className="text-base">User Growth</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="month" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip />
                <Area type="monotone" dataKey="users" stroke="hsl(221,83%,53%)" fill="hsl(221,83%,53%)" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">KYC & Transactions</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="month" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip />
                <Bar dataKey="kyc" fill="hsl(221,83%,53%)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="transactions" fill="hsl(142,71%,45%)" radius={[4, 4, 0, 0]} opacity={0.7} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {role === "admin" && (
        <Card>
          <CardHeader><CardTitle className="text-base">Recent Audit Log</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockAuditLog.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-medium text-sm">{entry.action}</TableCell>
                    <TableCell className="text-sm">{entry.actor}</TableCell>
                    <TableCell className="text-sm">{entry.target}</TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-[300px] truncate">{entry.details}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{new Date(entry.timestamp).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {role === "user" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center"><Fingerprint className="h-5 w-5 text-emerald-600" /></div>
              <div><p className="text-sm font-medium">Digital Identity</p><p className="text-xs text-muted-foreground">Active & Verified</p></div>
            </div>
            <p className="text-xs text-muted-foreground">DID:FIN:ETH:0x7a9f...3b2c</p>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center"><CreditCard className="h-5 w-5 text-blue-600" /></div>
              <div><p className="text-sm font-medium">Virtual Card</p><p className="text-xs text-muted-foreground">4532 •••• •••• 7891</p></div>
            </div>
            <p className="text-xs text-muted-foreground">Spend: ETB 12,500 / 50,000</p>
          </Card>
          <Card className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center"><KeyRound className="h-5 w-5 text-purple-600" /></div>
              <div><p className="text-sm font-medium">SSO Sessions</p><p className="text-xs text-muted-foreground">2 active sessions</p></div>
            </div>
            <p className="text-xs text-muted-foreground">Last login: Today, 08:00 AM</p>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
