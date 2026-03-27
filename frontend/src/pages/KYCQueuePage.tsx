import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { kycApi } from '@/services/api';
import { CheckCircle, XCircle, AlertTriangle, Clock, Eye } from 'lucide-react';

interface KYCSubmission {
  id: string;
  user_id: string;
  status: string;
  tier: string;
  full_name: string | null;
  date_of_birth: string | null;
  document_type: string | null;
  document_number: string | null;
  address: string | null;
  id_front_url: string | null;
  id_back_url: string | null;
  utility_bill_url: string | null;
  face_image_url: string | null;
  overall_confidence: number;
  risk_score: number;
  rejection_reason: string | null;
  reviewer_id: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
}

export default function KYCQueuePage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('pending');
  const [selectedKYC, setSelectedKYC] = useState<KYCSubmission | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject' | null>(null);
  const [selectedTier, setSelectedTier] = useState<string>('tier_1');
  const [reviewNotes, setReviewNotes] = useState('');
  
  const queryClient = useQueryClient();
  
  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ['kyc-queue', selectedStatus],
    queryFn: () => kycApi.listQueue(selectedStatus),
  });
  
  const approveMutation = useMutation({
    mutationFn: ({ id, tier, notes }: { id: string; tier: string; notes?: string }) =>
      kycApi.approve(id, tier, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kyc-queue'] });
      setReviewDialogOpen(false);
      setSelectedKYC(null);
      setReviewNotes('');
    },
  });
  
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      kycApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kyc-queue'] });
      setReviewDialogOpen(false);
      setSelectedKYC(null);
      setReviewNotes('');
    },
  });
  
  const handleReview = (kyc: KYCSubmission) => {
    setSelectedKYC(kyc);
    setReviewDialogOpen(true);
    setReviewAction(null);
  };
  
  const handleApprove = () => {
    if (!selectedKYC) return;
    approveMutation.mutate({
      id: selectedKYC.id,
      tier: selectedTier,
      notes: reviewNotes || undefined,
    });
  };
  
  const handleReject = () => {
    if (!selectedKYC || !reviewNotes.trim()) return;
    rejectMutation.mutate({
      id: selectedKYC.id,
      reason: reviewNotes,
    });
  };
  
  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any }> = {
      pending: { variant: 'secondary', icon: Clock },
      in_review: { variant: 'default', icon: Eye },
      approved: { variant: 'default', icon: CheckCircle },
      rejected: { variant: 'destructive', icon: XCircle },
      flagged: { variant: 'destructive', icon: AlertTriangle },
    };
    
    const config = variants[status] || variants.pending;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };
  
  const getRiskBadge = (score: number) => {
    if (score < 30) return <Badge variant="default">Low Risk</Badge>;
    if (score < 60) return <Badge variant="secondary">Medium Risk</Badge>;
    return <Badge variant="destructive">High Risk</Badge>;
  };
  
  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">KYC Review Queue</h1>
        <p className="text-muted-foreground mt-2">
          Review and approve user identity verifications
        </p>
      </div>
      
      <Tabs value={selectedStatus} onValueChange={setSelectedStatus}>
        <TabsList>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="in_review">In Review</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="rejected">Rejected</TabsTrigger>
          <TabsTrigger value="flagged">Flagged</TabsTrigger>
        </TabsList>
        
        <TabsContent value={selectedStatus} className="mt-6">
          {isLoading ? (
            <div className="text-center py-12">Loading submissions...</div>
          ) : submissions.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No submissions found with status: {selectedStatus}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {submissions.map((kyc: KYCSubmission) => (
                <Card key={kyc.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {kyc.full_name || 'Unknown Name'}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                          User ID: {kyc.user_id}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {getStatusBadge(kyc.status)}
                        {getRiskBadge(kyc.risk_score)}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Document Type</p>
                        <p className="font-medium">{kyc.document_type || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Document Number</p>
                        <p className="font-medium">{kyc.document_number || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">OCR Confidence</p>
                        <p className="font-medium">{(kyc.overall_confidence * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Submitted</p>
                        <p className="font-medium">
                          {kyc.submitted_at
                            ? new Date(kyc.submitted_at).toLocaleDateString()
                            : 'N/A'}
                        </p>
                      </div>
                    </div>
                    
                    {kyc.address && (
                      <div className="mb-4">
                        <p className="text-sm text-muted-foreground">Address</p>
                        <p className="font-medium">{kyc.address}</p>
                      </div>
                    )}
                    
                    {kyc.rejection_reason && (
                      <div className="mb-4 p-3 bg-destructive/10 rounded-md">
                        <p className="text-sm font-medium text-destructive">Rejection Reason:</p>
                        <p className="text-sm mt-1">{kyc.rejection_reason}</p>
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <Button onClick={() => handleReview(kyc)} variant="outline">
                        <Eye className="h-4 w-4 mr-2" />
                        Review Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
      
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Review KYC Submission</DialogTitle>
            <DialogDescription>
              Verify the submitted documents and approve or reject the application
            </DialogDescription>
          </DialogHeader>
          
          {selectedKYC && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Full Name</p>
                  <p className="text-sm text-muted-foreground">{selectedKYC.full_name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Date of Birth</p>
                  <p className="text-sm text-muted-foreground">{selectedKYC.date_of_birth || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Document Type</p>
                  <p className="text-sm text-muted-foreground">{selectedKYC.document_type || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Document Number</p>
                  <p className="text-sm text-muted-foreground">{selectedKYC.document_number || 'N/A'}</p>
                </div>
              </div>
              
              <div>
                <p className="text-sm font-medium mb-2">Address</p>
                <p className="text-sm text-muted-foreground">{selectedKYC.address || 'N/A'}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">OCR Confidence</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedKYC.overall_confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Risk Score</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedKYC.risk_score}/100
                  </p>
                </div>
              </div>
              
              <div>
                <p className="text-sm font-medium mb-3">Submitted Documents</p>
                <div className="grid grid-cols-2 gap-4">
                  {selectedKYC.id_front_url && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">ID Front</p>
                      <img
                        src={`/uploads/${selectedKYC.id_front_url}`}
                        alt="ID Front"
                        className="w-full rounded border"
                      />
                    </div>
                  )}
                  {selectedKYC.id_back_url && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">ID Back</p>
                      <img
                        src={`/uploads/${selectedKYC.id_back_url}`}
                        alt="ID Back"
                        className="w-full rounded border"
                      />
                    </div>
                  )}
                  {selectedKYC.utility_bill_url && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Utility Bill</p>
                      <img
                        src={`/uploads/${selectedKYC.utility_bill_url}`}
                        alt="Utility Bill"
                        className="w-full rounded border"
                      />
                    </div>
                  )}
                  {selectedKYC.face_image_url && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Face Photo</p>
                      <img
                        src={`/uploads/${selectedKYC.face_image_url}`}
                        alt="Face"
                        className="w-full rounded border"
                      />
                    </div>
                  )}
                </div>
              </div>
              
              {reviewAction === 'approve' && (
                <div className="space-y-4 p-4 bg-green-50 dark:bg-green-950 rounded-lg">
                  <div>
                    <label className="text-sm font-medium">Approve as Tier</label>
                    <Select value={selectedTier} onValueChange={setSelectedTier}>
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tier_1">Tier 1 (Basic)</SelectItem>
                        <SelectItem value="tier_2">Tier 2 (Enhanced)</SelectItem>
                        <SelectItem value="tier_3">Tier 3 (Full)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Notes (optional)</label>
                    <Textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Add any notes about this approval..."
                      className="mt-2"
                    />
                  </div>
                </div>
              )}
              
              {reviewAction === 'reject' && (
                <div className="space-y-4 p-4 bg-red-50 dark:bg-red-950 rounded-lg">
                  <div>
                    <label className="text-sm font-medium">Rejection Reason *</label>
                    <Textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Explain why this KYC is being rejected..."
                      className="mt-2"
                      required
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            {!reviewAction ? (
              <>
                <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
                  Close
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => setReviewAction('reject')}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  variant="default"
                  onClick={() => setReviewAction('approve')}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </>
            ) : reviewAction === 'approve' ? (
              <>
                <Button variant="outline" onClick={() => setReviewAction(null)}>
                  Back
                </Button>
                <Button
                  onClick={handleApprove}
                  disabled={approveMutation.isPending}
                >
                  Confirm Approval
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={() => setReviewAction(null)}>
                  Back
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleReject}
                  disabled={rejectMutation.isPending || !reviewNotes.trim()}
                >
                  Confirm Rejection
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
