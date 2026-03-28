import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { kycApi, identityApi } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, Mail, Phone, Shield } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function KYCApproverUserPage() {
  const { userId } = useParams<{ userId: string }>();
  const { toast } = useToast();
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["kyc-approver-detail", userId],
    queryFn: () => kycApi.getApproverUserDetail(userId!),
    enabled: !!userId,
  });

  const verifyEmail = useMutation({
    mutationFn: () => identityApi.verifyEmailManual(userId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kyc-approver-detail", userId] });
      toast({ title: "Email marked verified" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const verifyPhone = useMutation({
    mutationFn: () => identityApi.verifyPhoneManual(userId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kyc-approver-detail", userId] });
      toast({ title: "Phone marked verified" });
    },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  if (!userId) {
    return <div className="container py-8 text-muted-foreground">Missing user id</div>;
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container py-8">
        <p className="text-destructive">{error instanceof Error ? error.message : "Failed to load"}</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link to="/kyc-queue">Back to queue</Link>
        </Button>
      </div>
    );
  }

  const { user, kyc, trust } = data;

  return (
    <div className="container max-w-4xl mx-auto py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/kyc-queue" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Queue
          </Link>
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold">Applicant profile</h1>
        <p className="text-muted-foreground text-sm mt-1">User ID: {user.id}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account</CardTitle>
          <CardDescription>Contact and verification</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Email</p>
              <p className="font-medium">{user.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant={user.is_email_verified ? "default" : "secondary"}>
                  {user.is_email_verified ? "Verified" : "Unverified"}
                </Badge>
                {!user.is_email_verified && (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={verifyEmail.isPending}
                    onClick={() => verifyEmail.mutate()}
                  >
                    <Mail className="h-3.5 w-3.5 mr-1" /> Verify email
                  </Button>
                )}
              </div>
            </div>
            <div>
              <p className="text-muted-foreground">Phone</p>
              <p className="font-medium">{user.phone_number || "—"}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant={user.phone_verified ? "default" : "secondary"}>
                  {user.phone_verified ? "Verified" : "Unverified"}
                </Badge>
                {!user.phone_verified && (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={verifyPhone.isPending}
                    onClick={() => verifyPhone.mutate()}
                  >
                    <Phone className="h-3.5 w-3.5 mr-1" /> Verify phone
                  </Button>
                )}
              </div>
            </div>
            <div>
              <p className="text-muted-foreground">Username</p>
              <p className="font-medium">{user.username}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Full name</p>
              <p className="font-medium">{user.full_name || "—"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="h-5 w-5" /> Trust score
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6 items-center text-sm">
          <div>
            <p className="text-muted-foreground">Score</p>
            <p className="text-2xl font-bold">{Math.round(trust.trust_score)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Risk</p>
            <Badge>{trust.risk_level}</Badge>
          </div>
          <div>
            <p className="text-muted-foreground">KYC tier (trust engine)</p>
            <p className="font-medium">Tier {trust.kyc_tier}</p>
          </div>
        </CardContent>
      </Card>

      {kyc ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">KYC record</CardTitle>
            <CardDescription>
              Status: <span className="capitalize">{kyc.status}</span> · Tier: {kyc.tier}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-3 text-sm">
              <div className="flex justify-between gap-2">
                <span className="text-muted-foreground">Document</span>
                <span className="font-medium">{kyc.document_type || "—"}</span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-muted-foreground">Doc number</span>
                <span className="font-mono text-xs">{kyc.document_number || "—"}</span>
              </div>
              <div className="flex justify-between gap-2 sm:col-span-2">
                <span className="text-muted-foreground">Address</span>
                <span className="font-medium text-right">{kyc.address || "—"}</span>
              </div>
            </div>
            {kyc.extracted_data && typeof kyc.extracted_data === "object" && (
              <div className="rounded-lg border bg-muted/30 p-3 text-xs space-y-2">
                <p className="font-medium text-foreground">Extracted data (JSON)</p>
                <div className="grid sm:grid-cols-2 gap-3">
                  {Object.entries(kyc.extracted_data as Record<string, unknown>).map(([k, v]) => (
                    <div key={k} className="space-y-1">
                      <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}</span>
                      <pre className="whitespace-pre-wrap break-all text-[11px] bg-background rounded p-2 border max-h-40 overflow-auto">
                        {typeof v === "object" ? JSON.stringify(v, null, 2) : String(v)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-muted-foreground text-sm">No KYC submission for this user.</CardContent>
        </Card>
      )}
    </div>
  );
}
