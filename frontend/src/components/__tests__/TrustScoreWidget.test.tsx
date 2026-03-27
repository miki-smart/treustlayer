import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TrustScoreWidget } from '../TrustScoreWidget';

const mockTrustProfile = {
  user_id: 'user-123',
  trust_score: 85,
  risk_level: 'low',
  email_verified: true,
  phone_verified: true,
  kyc_tier: 2,
  face_verified: true,
  voice_verified: true,
  digital_identity_active: true,
  account_age_days: 180,
  last_calculated_at: new Date().toISOString(),
};

describe('TrustScoreWidget', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const renderWidget = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <TrustScoreWidget {...props} />
      </QueryClientProvider>
    );
  };

  it('should render loading state', () => {
    renderWidget();
    expect(screen.getByRole('status') || screen.getByText(/loading/i)).toBeTruthy();
  });

  it('should display trust score', async () => {
    vi.mock('@/services/api', () => ({
      trustApi: {
        getProfile: vi.fn().mockResolvedValue(mockTrustProfile),
      },
    }));

    renderWidget();
    
    const score = await screen.findByText('85');
    expect(score).toBeInTheDocument();
  });

  it('should show low risk badge for high score', async () => {
    vi.mock('@/services/api', () => ({
      trustApi: {
        getProfile: vi.fn().mockResolvedValue(mockTrustProfile),
      },
    }));

    renderWidget();
    
    const badge = await screen.findByText(/LOW RISK/i);
    expect(badge).toBeInTheDocument();
  });

  it('should show verification checkmarks', async () => {
    vi.mock('@/services/api', () => ({
      trustApi: {
        getProfile: vi.fn().mockResolvedValue(mockTrustProfile),
      },
    }));

    renderWidget();
    
    const emailVerified = await screen.findByText(/Email Verified/i);
    expect(emailVerified).toBeInTheDocument();
  });

  it('should show refresh button when showRefresh is true', async () => {
    vi.mock('@/services/api', () => ({
      trustApi: {
        getProfile: vi.fn().mockResolvedValue(mockTrustProfile),
      },
    }));

    renderWidget({ showRefresh: true });
    
    const refreshButton = await screen.findByText(/Recalculate/i);
    expect(refreshButton).toBeInTheDocument();
  });
});
