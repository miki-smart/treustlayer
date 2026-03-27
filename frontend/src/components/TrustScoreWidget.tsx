import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { trustApi } from '@/services/api';
import { Shield, ShieldCheck, ShieldAlert, RefreshCw } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface TrustScoreWidgetProps {
  userId?: string;
  showRefresh?: boolean;
}

export function TrustScoreWidget({ userId, showRefresh = false }: TrustScoreWidgetProps) {
  const { data: profile, isLoading, refetch } = useQuery({
    queryKey: ['trust-profile', userId],
    queryFn: () => (userId ? trustApi.getUserProfile(userId) : trustApi.getProfile()),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent mx-auto" />
        </CardContent>
      </Card>
    );
  }

  if (!profile) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Trust profile not available
        </CardContent>
      </Card>
    );
  }

  const getRiskIcon = () => {
    if (profile.risk_level === 'low') return <ShieldCheck className="h-5 w-5 text-green-500" />;
    if (profile.risk_level === 'medium') return <Shield className="h-5 w-5 text-yellow-500" />;
    return <ShieldAlert className="h-5 w-5 text-red-500" />;
  };

  const getRiskBadge = () => {
    const variants: Record<string, any> = {
      low: 'default',
      medium: 'secondary',
      high: 'destructive',
    };
    return (
      <Badge variant={variants[profile.risk_level] || 'secondary'}>
        {profile.risk_level.toUpperCase()} RISK
      </Badge>
    );
  };

  const getScoreColor = () => {
    if (profile.trust_score >= 80) return 'text-green-600 dark:text-green-400';
    if (profile.trust_score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {getRiskIcon()}
            Trust Score
          </CardTitle>
          {getRiskBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center">
          <div className={`text-5xl font-bold ${getScoreColor()}`}>
            {profile.trust_score.toFixed(0)}
          </div>
          <p className="text-sm text-muted-foreground mt-1">out of 100</p>
        </div>

        <Progress value={profile.trust_score} className="h-2" />

        <div className="space-y-2 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Email Verified</span>
            <span className={profile.email_verified ? 'text-green-600' : 'text-gray-400'}>
              {profile.email_verified ? '✓' : '✗'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Phone Verified</span>
            <span className={profile.phone_verified ? 'text-green-600' : 'text-gray-400'}>
              {profile.phone_verified ? '✓' : '✗'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">KYC Tier</span>
            <Badge variant="outline">Tier {profile.kyc_tier}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Face Biometric</span>
            <span className={profile.face_verified ? 'text-green-600' : 'text-gray-400'}>
              {profile.face_verified ? '✓' : '✗'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Voice Biometric</span>
            <span className={profile.voice_verified ? 'text-green-600' : 'text-gray-400'}>
              {profile.voice_verified ? '✓' : '✗'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Digital Identity</span>
            <span className={profile.digital_identity_active ? 'text-green-600' : 'text-gray-400'}>
              {profile.digital_identity_active ? '✓' : '✗'}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Account Age</span>
            <span>{profile.account_age_days} days</span>
          </div>
        </div>

        {showRefresh && (
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="w-full mt-4"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Recalculate Score
          </Button>
        )}

        <p className="text-xs text-muted-foreground text-center pt-2">
          Last updated: {new Date(profile.last_calculated_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}
