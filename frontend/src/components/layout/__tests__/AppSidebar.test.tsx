import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { AppSidebar } from '../AppSidebar';

describe('AppSidebar', () => {
  const renderSidebar = (user: any) => {
    vi.mock('@/contexts/AuthContext', () => ({
      useAuth: () => ({
        user,
        isAuthenticated: !!user,
        hasRole: (role: string) => user?.role === role,
      }),
      AuthProvider: ({ children }: any) => children,
    }));

    return render(
      <BrowserRouter>
        <AuthProvider>
          <AppSidebar />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  it('should show user navigation items', () => {
    const user = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user',
    };

    renderSidebar(user);
    
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Profile/i)).toBeInTheDocument();
  });

  it('should show admin navigation items', () => {
    const admin = {
      id: 'admin-123',
      email: 'admin@example.com',
      role: 'admin',
    };

    renderSidebar(admin);
    
    expect(screen.getByText(/Admin Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/KYC Queue/i)).toBeInTheDocument();
    expect(screen.getByText(/App Approvals/i)).toBeInTheDocument();
    expect(screen.getByText(/Audit Logs/i)).toBeInTheDocument();
  });

  it('should show KYC approver navigation items', () => {
    const kycApprover = {
      id: 'kyc-123',
      email: 'kyc@example.com',
      role: 'kyc_approver',
    };

    renderSidebar(kycApprover);
    
    expect(screen.getByText(/KYC Queue/i)).toBeInTheDocument();
  });

  it('should show app owner navigation items', () => {
    const appOwner = {
      id: 'owner-123',
      email: 'owner@example.com',
      role: 'app_owner',
    };

    renderSidebar(appOwner);
    
    expect(screen.getByText(/My Apps/i)).toBeInTheDocument();
  });

  it('should not show admin items to regular user', () => {
    const user = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user',
    };

    renderSidebar(user);
    
    expect(screen.queryByText(/Admin Dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/App Approvals/i)).not.toBeInTheDocument();
  });

  it('should not show KYC queue to app owner', () => {
    const appOwner = {
      id: 'owner-123',
      email: 'owner@example.com',
      role: 'app_owner',
    };

    renderSidebar(appOwner);
    
    expect(screen.queryByText(/KYC Queue/i)).not.toBeInTheDocument();
  });
});
