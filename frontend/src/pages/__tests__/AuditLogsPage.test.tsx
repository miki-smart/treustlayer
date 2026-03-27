import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tantml:react-query';
import { BrowserRouter } from 'react-router-dom';
import AuditLogsPage from '../AuditLogsPage';

const mockAuditEntries = [
  {
    id: 'audit-1',
    actor_id: 'admin-123',
    action: 'user.created',
    resource_type: 'user',
    resource_id: 'user-456',
    metadata: { ip_address: '127.0.0.1' },
    changes: {},
    timestamp: new Date().toISOString(),
  },
  {
    id: 'audit-2',
    actor_id: 'admin-123',
    action: 'kyc.approved',
    resource_type: 'kyc',
    resource_id: 'kyc-789',
    metadata: { ip_address: '127.0.0.1' },
    changes: { status: { old: 'pending', new: 'approved' } },
    timestamp: new Date().toISOString(),
  },
];

describe('AuditLogsPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuditLogsPage />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should render page title', () => {
    renderPage();
    expect(screen.getByText(/Audit Logs/i)).toBeInTheDocument();
  });

  it('should render filters section', () => {
    renderPage();
    expect(screen.getByText(/Filters/i)).toBeInTheDocument();
  });

  it('should display audit entries', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAuditEntries,
    });

    renderPage();
    
    const action = await screen.findByText('user.created');
    expect(action).toBeInTheDocument();
  });

  it('should show action badges', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAuditEntries,
    });

    renderPage();
    
    const createdBadge = await screen.findByText(/Created/i);
    expect(createdBadge).toBeInTheDocument();
  });

  it('should show resource type', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAuditEntries,
    });

    renderPage();
    
    const resourceTypes = await screen.findAllByText(/user|kyc/i);
    expect(resourceTypes.length).toBeGreaterThan(0);
  });

  it('should have filter dropdowns', () => {
    renderPage();
    
    expect(screen.getByText(/Action/i)).toBeInTheDocument();
    expect(screen.getByText(/Resource Type/i)).toBeInTheDocument();
  });
});
