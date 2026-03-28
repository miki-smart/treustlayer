import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, CheckCircle, Clock, FileText, Activity } from 'lucide-react';
import { dashboardApi, type DashboardStats } from '@/services/api';

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.getStats(),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12">Loading dashboard...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12 text-muted-foreground">
          Failed to load dashboard statistics
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      icon: Users,
      description: `${stats.verified_users} verified`,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-950',
    },
    {
      title: 'KYC Pending',
      value: stats.kyc_pending,
      icon: Clock,
      description: `${stats.kyc_in_review} in review`,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50 dark:bg-yellow-950',
    },
    {
      title: 'KYC Approved',
      value: stats.kyc_approved,
      icon: CheckCircle,
      description: `${stats.kyc_rejected} rejected`,
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-950',
    },
    {
      title: 'Total Apps',
      value: stats.total_apps,
      icon: FileText,
      description: `${stats.apps_pending} pending approval`,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-950',
    },
    {
      title: 'Active Sessions',
      value: stats.active_sessions,
      icon: Activity,
      description: 'Currently active',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50 dark:bg-indigo-950',
    },
  ];

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          System overview and analytics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>KYC Status Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Pending</span>
                <span className="font-semibold">{stats.kyc_pending}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">In Review</span>
                <span className="font-semibold">{stats.kyc_in_review}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Approved</span>
                <span className="font-semibold text-green-600">{stats.kyc_approved}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Rejected</span>
                <span className="font-semibold text-red-600">{stats.kyc_rejected}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>App Registry Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Apps</span>
                <span className="font-semibold">{stats.total_apps}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Pending Approval</span>
                <span className="font-semibold text-yellow-600">{stats.apps_pending}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Approved</span>
                <span className="font-semibold text-green-600">
                  {stats.total_apps - stats.apps_pending}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm">All systems operational</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm">Database: Connected</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm">API: Healthy</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
