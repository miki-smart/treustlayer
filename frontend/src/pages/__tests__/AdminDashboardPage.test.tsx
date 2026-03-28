import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import AdminDashboardPage from '../AdminDashboardPage';

const mockStats = {
  total_users: 150,
  verified_users: 120,
  kyc_pending: 10,
  kyc_in_review: 5,
  kyc_approved: 100,
  kyc_rejected: 8,
  total_apps: 25,
  apps_pending: 3,
  active_sessions: 85,
};

describe('AdminDashboardPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  beforeEach(() => {
    queryClient.clear();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockStats,
    });
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AdminDashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should render page title', async () => {
    renderPage();
    expect(await screen.findByText(/Admin Dashboard/i)).toBeInTheDocument();
  });

  it('should display statistics cards', async () => {
    renderPage();
    
    const totalUsers = await screen.findByText('150');
    expect(totalUsers).toBeInTheDocument();
  });

  it('should show total users stat', async () => {
    renderPage();
    
    expect(await screen.findByText(/Total Users/i)).toBeInTheDocument();
    expect(await screen.findByText('150')).toBeInTheDocument();
  });

  it('should show KYC stats', async () => {
    renderPage();

    expect(await screen.findByText(/KYC Pending/i)).toBeInTheDocument();
    const tens = await screen.findAllByText('10');
    expect(tens.length).toBeGreaterThanOrEqual(1);
  });

  it('should show active sessions', async () => {
    renderPage();
    
    expect(await screen.findByText(/Active Sessions/i)).toBeInTheDocument();
    expect(await screen.findByText('85')).toBeInTheDocument();
  });

  it('should show system health', async () => {
    renderPage();
    
    expect(await screen.findByText(/System Health/i)).toBeInTheDocument();
    expect(await screen.findByText(/All systems operational/i)).toBeInTheDocument();
  });
});
