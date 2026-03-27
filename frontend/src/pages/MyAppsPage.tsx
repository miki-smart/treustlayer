import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { appsApi } from '@/services/api';
import { Plus, Key, Copy, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface App {
  id: string;
  name: string;
  client_id: string;
  client_secret?: string;
  api_key?: string;
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

export default function MyAppsPage() {
  const [registerDialogOpen, setRegisterDialogOpen] = useState(false);
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);
  const [newApp, setNewApp] = useState({
    name: '',
    description: '',
    category: 'general',
    allowed_scopes: 'openid,profile,email',
    redirect_uris: '',
  });
  const [registeredCredentials, setRegisteredCredentials] = useState<{
    client_id: string;
    client_secret: string;
    api_key: string;
  } | null>(null);
  
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const { data: apps = [], isLoading } = useQuery({
    queryKey: ['my-apps'],
    queryFn: () => appsApi.mine(),
  });
  
  const registerMutation = useMutation({
    mutationFn: (data: any) => appsApi.register(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['my-apps'] });
      setRegisterDialogOpen(false);
      setRegisteredCredentials({
        client_id: data.client_id,
        client_secret: data.client_secret || '',
        api_key: data.api_key || '',
      });
      setCredentialsDialogOpen(true);
      setNewApp({
        name: '',
        description: '',
        category: 'general',
        allowed_scopes: 'openid,profile,email',
        redirect_uris: '',
      });
    },
  });
  
  const handleRegister = () => {
    registerMutation.mutate({
      name: newApp.name,
      description: newApp.description,
      category: newApp.category,
      allowed_scopes: newApp.allowed_scopes.split(',').map(s => s.trim()),
      redirect_uris: newApp.redirect_uris.split('\n').map(s => s.trim()).filter(Boolean),
    });
  };
  
  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: `${label} copied to clipboard` });
  };
  
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">My Applications</h1>
          <p className="text-muted-foreground mt-2">
            Manage your OAuth2 client applications
          </p>
        </div>
        <Button onClick={() => setRegisterDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Register New App
        </Button>
      </div>
      
      {isLoading ? (
        <div className="text-center py-12">Loading apps...</div>
      ) : apps.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">No applications registered yet</p>
            <Button onClick={() => setRegisterDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Register Your First App
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {apps.map((app: App) => (
            <Card key={app.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{app.name}</CardTitle>
                    <CardDescription className="mt-2">{app.description}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {app.is_approved ? (
                      <Badge variant="default" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        Approved
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <XCircle className="h-3 w-3" />
                        Pending Approval
                      </Badge>
                    )}
                    {app.is_active ? (
                      <Badge variant="default">Active</Badge>
                    ) : (
                      <Badge variant="destructive">Inactive</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                    <div>
                      <p className="text-sm font-medium">Client ID</p>
                      <p className="text-sm font-mono text-muted-foreground">{app.client_id}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(app.client_id, 'Client ID')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Category</p>
                      <p className="font-medium">{app.category}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Created</p>
                      <p className="font-medium">
                        {new Date(app.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Allowed Scopes</p>
                    <div className="flex flex-wrap gap-2">
                      {app.allowed_scopes.map((scope) => (
                        <Badge key={scope} variant="outline">
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
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      <Dialog open={registerDialogOpen} onOpenChange={setRegisterDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Register New Application</DialogTitle>
            <DialogDescription>
              Create a new OAuth2 client application
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>App Name *</Label>
              <Input
                value={newApp.name}
                onChange={(e) => setNewApp({ ...newApp, name: e.target.value })}
                placeholder="My Awesome App"
              />
            </div>
            
            <div>
              <Label>Description</Label>
              <Textarea
                value={newApp.description}
                onChange={(e) => setNewApp({ ...newApp, description: e.target.value })}
                placeholder="What does your app do?"
              />
            </div>
            
            <div>
              <Label>Category</Label>
              <Input
                value={newApp.category}
                onChange={(e) => setNewApp({ ...newApp, category: e.target.value })}
                placeholder="general, finance, health, etc."
              />
            </div>
            
            <div>
              <Label>Allowed Scopes (comma-separated) *</Label>
              <Input
                value={newApp.allowed_scopes}
                onChange={(e) => setNewApp({ ...newApp, allowed_scopes: e.target.value })}
                placeholder="openid,profile,email,kyc_status"
              />
            </div>
            
            <div>
              <Label>Redirect URIs (one per line) *</Label>
              <Textarea
                value={newApp.redirect_uris}
                onChange={(e) => setNewApp({ ...newApp, redirect_uris: e.target.value })}
                placeholder="http://localhost:3000/callback&#10;https://myapp.com/callback"
                rows={3}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setRegisterDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleRegister}
              disabled={registerMutation.isPending || !newApp.name || !newApp.redirect_uris}
            >
              Register App
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <Dialog open={credentialsDialogOpen} onOpenChange={setCredentialsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              App Credentials
            </DialogTitle>
            <DialogDescription>
              Save these credentials securely. They will not be shown again.
            </DialogDescription>
          </DialogHeader>
          
          {registeredCredentials && (
            <div className="space-y-4">
              <div className="p-4 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-md">
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Important: Copy these credentials now. You won't be able to see them again.
                </p>
              </div>
              
              <div className="space-y-3">
                <div className="p-3 bg-muted rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label>Client ID</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(registeredCredentials.client_id, 'Client ID')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="font-mono text-sm break-all">{registeredCredentials.client_id}</p>
                </div>
                
                <div className="p-3 bg-muted rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label>Client Secret</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(registeredCredentials.client_secret, 'Client Secret')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="font-mono text-sm break-all">{registeredCredentials.client_secret}</p>
                </div>
                
                <div className="p-3 bg-muted rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <Label>API Key</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(registeredCredentials.api_key, 'API Key')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="font-mono text-sm break-all">{registeredCredentials.api_key}</p>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setCredentialsDialogOpen(false)}>
              I've Saved My Credentials
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
