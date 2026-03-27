import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, User, Shield, Database } from 'lucide-react';

interface AuditEntry {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata: Record<string, any>;
  changes: Record<string, any>;
  timestamp: string;
}

export default function AuditLogsPage() {
  const [filterAction, setFilterAction] = useState<string>('');
  const [filterResourceType, setFilterResourceType] = useState<string>('');
  const [searchUserId, setSearchUserId] = useState<string>('');
  
  const { data: entries = [], isLoading } = useQuery<AuditEntry[]>({
    queryKey: ['audit-logs', filterAction, filterResourceType],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterAction) params.append('action', filterAction);
      if (filterResourceType) params.append('resource_type', filterResourceType);
      
      const response = await fetch(`/api/v1/audit/entries?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch audit logs');
      return response.json();
    },
  });
  
  const getActionBadge = (action: string) => {
    if (action.includes('created')) return <Badge variant="default">Created</Badge>;
    if (action.includes('updated')) return <Badge variant="secondary">Updated</Badge>;
    if (action.includes('deleted')) return <Badge variant="destructive">Deleted</Badge>;
    if (action.includes('approved')) return <Badge variant="default">Approved</Badge>;
    if (action.includes('rejected')) return <Badge variant="destructive">Rejected</Badge>;
    return <Badge variant="outline">{action}</Badge>;
  };
  
  const getResourceIcon = (resourceType: string) => {
    if (resourceType === 'user') return <User className="h-4 w-4" />;
    if (resourceType === 'kyc') return <Shield className="h-4 w-4" />;
    if (resourceType === 'app') return <FileText className="h-4 w-4" />;
    return <Database className="h-4 w-4" />;
  };
  
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Audit Logs</h1>
        <p className="text-muted-foreground mt-2">
          Immutable audit trail for compliance and security
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Action</label>
              <Select value={filterAction} onValueChange={setFilterAction}>
                <SelectTrigger>
                  <SelectValue placeholder="All actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All actions</SelectItem>
                  <SelectItem value="user.created">User Created</SelectItem>
                  <SelectItem value="user.updated">User Updated</SelectItem>
                  <SelectItem value="kyc.submitted">KYC Submitted</SelectItem>
                  <SelectItem value="kyc.approved">KYC Approved</SelectItem>
                  <SelectItem value="kyc.rejected">KYC Rejected</SelectItem>
                  <SelectItem value="app.registered">App Registered</SelectItem>
                  <SelectItem value="app.approved">App Approved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Resource Type</label>
              <Select value={filterResourceType} onValueChange={setFilterResourceType}>
                <SelectTrigger>
                  <SelectValue placeholder="All resources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All resources</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="kyc">KYC</SelectItem>
                  <SelectItem value="app">App</SelectItem>
                  <SelectItem value="consent">Consent</SelectItem>
                  <SelectItem value="session">Session</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">User ID</label>
              <Input
                value={searchUserId}
                onChange={(e) => setSearchUserId(e.target.value)}
                placeholder="Search by user ID"
              />
            </div>
          </div>
        </CardContent>
      </Card>
      
      {isLoading ? (
        <div className="text-center py-12">Loading audit logs...</div>
      ) : entries.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No audit entries found
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <Card key={entry.id}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 bg-muted rounded-md mt-1">
                      {getResourceIcon(entry.resource_type)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getActionBadge(entry.action)}
                        <span className="text-sm text-muted-foreground">
                          {entry.resource_type}
                        </span>
                      </div>
                      
                      <p className="text-sm font-medium mb-2">{entry.action}</p>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-muted-foreground">
                        {entry.actor_id && (
                          <div>
                            <span className="font-medium">Actor:</span> {entry.actor_id.slice(0, 8)}...
                          </div>
                        )}
                        {entry.resource_id && (
                          <div>
                            <span className="font-medium">Resource:</span> {entry.resource_id.slice(0, 8)}...
                          </div>
                        )}
                        {entry.metadata.ip_address && (
                          <div>
                            <span className="font-medium">IP:</span> {entry.metadata.ip_address}
                          </div>
                        )}
                        <div>
                          <span className="font-medium">Time:</span>{' '}
                          {new Date(entry.timestamp).toLocaleString()}
                        </div>
                      </div>
                      
                      {Object.keys(entry.changes).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-muted-foreground cursor-pointer">
                            View changes
                          </summary>
                          <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-x-auto">
                            {JSON.stringify(entry.changes, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-xs text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
