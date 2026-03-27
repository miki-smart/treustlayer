import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { appsApi } from '@/services/api';
import { CheckCircle, XCircle, ExternalLink, Shield } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface App {
  id: string;
  name: string;
  client_id: string;
  owner_id: string;
  allowed_scopes: string[];
  redirect_uris: string[];
  description: string;
  logo_url?: string;
  category: string;
  is_active: boolean;
  is_approved: boolean;
  is_public: boolean;
  created_at: string;
}

export default function AppApprovalPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const { data: apps = [], isLoading } = useQuery({
    queryKey: ['all-apps'],
    queryFn: () => appsApi.list(),
  });
  
  const approveMutation = useMutation({
    mutationFn: (appId: string) => appsApi.approve(appId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-apps'] });
      toast({ title: 'App approved successfully' });
    },
  });
  
  const deactivateMutation = useMutation({
    mutationFn: (appId: string) => appsApi.deactivate(appId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-apps'] });
      toast({ title: 'App deactivated' });
    },
  });
  
  const pendingApps = apps.filter((app: App) => !app.is_approved);
  const approvedApps = apps.filter((app: App) => app.is_approved);
  
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">App Registry Management</h1>
        <p className="text-muted-foreground mt-2">
          Review and approve OAuth2 client applications
        </p>
      </div>
      
      {pendingApps.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Pending Approval</h2>
          <div className="grid gap-4">
            {pendingApps.map((app: App) => (
              <Card key={app.id} className="border-yellow-200 dark:border-yellow-800">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{app.name}</CardTitle>
                      <CardDescription className="mt-2">{app.description}</CardDescription>
                    </div>
                    <Badge variant="secondary">Pending</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Client ID</p>
                        <p className="font-mono text-sm">{app.client_id}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Category</p>
                        <p className="font-medium">{app.category}</p>
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Requested Scopes</p>
                      <div className="flex flex-wrap gap-2">
                        {app.allowed_scopes.map((scope) => (
                          <Badge key={scope} variant="outline">
                            <Shield className="h-3 w-3 mr-1" />
                            {scope}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Redirect URIs</p>
                      <div className="space-y-1">
                        {app.redirect_uris.map((uri, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            <ExternalLink className="h-3 w-3 text-muted-foreground" />
                            <span className="font-mono text-xs">{uri}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex gap-2 pt-4 border-t">
                      <Button
                        onClick={() => approveMutation.mutate(app.id)}
                        disabled={approveMutation.isPending}
                        className="gap-2"
                      >
                        <CheckCircle className="h-4 w-4" />
                        Approve
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={() => deactivateMutation.mutate(app.id)}
                        disabled={deactivateMutation.isPending}
                        className="gap-2"
                      >
                        <XCircle className="h-4 w-4" />
                        Reject
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
      
      {approvedApps.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Approved Applications</h2>
          <div className="grid gap-4">
            {approvedApps.map((app: App) => (
              <Card key={app.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{app.name}</CardTitle>
                      <CardDescription className="mt-2">{app.description}</CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="default" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        Approved
                      </Badge>
                      {app.is_active ? (
                        <Badge variant="default">Active</Badge>
                      ) : (
                        <Badge variant="destructive">Inactive</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Client ID</p>
                      <p className="font-mono text-sm">{app.client_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Category</p>
                      <p className="font-medium">{app.category}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
