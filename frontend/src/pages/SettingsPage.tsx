import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { identityApi, authApi } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { UserCircle, Shield, Bell, Key, Monitor, Loader2, CheckCircle2 } from "lucide-react";

const SettingsPage = () => {
  const { user, role, refreshUser } = useAuth();
  const { toast } = useToast();
  const [fullName, setFullName] = useState(user?.full_name || user?.name || "");
  const [phone, setPhone] = useState(user?.phone_number || "");
  const [currentPwd, setCurrentPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");

  const profileMutation = useMutation({
    mutationFn: () => identityApi.updateUser(user!.id, { full_name: fullName, phone_number: phone }),
    onSuccess: () => { refreshUser(); toast({ title: "Profile updated" }); },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const passwordMutation = useMutation({
    mutationFn: () => authApi.changePassword(user!.id, currentPwd, newPwd),
    onSuccess: () => { setCurrentPwd(""); setNewPwd(""); toast({ title: "Password changed" }); },
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  const verifyEmailMutation = useMutation({
    mutationFn: () => authApi.sendVerificationEmail(),
    onSuccess: () => toast({ title: "Verification email sent", description: "Check your inbox." }),
    onError: (e: Error) => toast({ title: "Error", description: e.message, variant: "destructive" }),
  });

  return (
    <div>
      <PageHeader title="Settings" description="Manage your account and security preferences" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile */}
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><UserCircle className="h-4 w-4" /> Profile Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Full Name</label>
                <Input value={fullName} onChange={e => setFullName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Email</label>
                <div className="relative">
                  <Input defaultValue={user?.email} disabled />
                  {user?.is_email_verified ? (
                    <CheckCircle2 className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
                  ) : (
                    <button
                      type="button"
                      onClick={() => verifyEmailMutation.mutate()}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-primary hover:underline"
                    >
                      Verify
                    </button>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Phone</label>
                <Input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+251911234567" />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Username</label>
                <Input defaultValue={user?.username} disabled />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Role</label>
                <Input defaultValue={role} disabled />
              </div>
            </div>
            <Button size="sm" disabled={profileMutation.isPending} onClick={() => profileMutation.mutate()}>
              {profileMutation.isPending ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Saving…</> : "Save Changes"}
            </Button>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Shield className="h-4 w-4" /> Security</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: "Two-factor Auth", desc: "Protect your account", enabled: true },
              { label: "Biometric Login", desc: "Use face/voice to login", enabled: true },
              { label: "Login Alerts", desc: "Get notified of new logins", enabled: false },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <div><p className="text-sm font-medium">{item.label}</p><p className="text-xs text-muted-foreground">{item.desc}</p></div>
                <Switch defaultChecked={item.enabled} />
              </div>
            ))}
            <div className="space-y-2 pt-2 border-t">
              <p className="text-sm font-medium">Change Password</p>
              <Input type="password" placeholder="Current password" value={currentPwd} onChange={e => setCurrentPwd(e.target.value)} />
              <Input type="password" placeholder="New password" value={newPwd} onChange={e => setNewPwd(e.target.value)} />
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                disabled={!currentPwd || !newPwd || passwordMutation.isPending}
                onClick={() => passwordMutation.mutate()}
              >
                <Key className="mr-2 h-3 w-3" />
                {passwordMutation.isPending ? "Updating…" : "Update Password"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="lg:col-span-3">
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Bell className="h-4 w-4" /> Notification Preferences</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { label: "Transaction Alerts", desc: "Card payments, transfers" },
                { label: "Security Alerts", desc: "Login attempts, changes" },
                { label: "KYC Updates", desc: "Application status changes" },
                { label: "Identity Changes", desc: "Credential updates" },
                { label: "SSO Sessions", desc: "New sessions, expirations" },
                { label: "System Updates", desc: "Maintenance, new features" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-muted/20">
                  <div><p className="text-sm font-medium">{item.label}</p><p className="text-xs text-muted-foreground">{item.desc}</p></div>
                  <Switch defaultChecked />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage;
