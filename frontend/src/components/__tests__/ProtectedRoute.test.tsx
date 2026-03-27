import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';

const TestComponent = () => <div>Protected Content</div>;

describe('ProtectedRoute', () => {
  const renderProtectedRoute = (user: any = null) => {
    vi.mock('@/contexts/AuthContext', () => ({
      useAuth: () => ({
        user,
        isLoading: false,
        isAuthenticated: !!user,
      }),
      AuthProvider: ({ children }: any) => children,
    }));

    return render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
  };

  it('should redirect to login when not authenticated', () => {
    renderProtectedRoute(null);
    
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should render children when authenticated', () => {
    const user = {
      id: 'user-123',
      email: 'test@example.com',
      role: 'user',
    };
    
    renderProtectedRoute(user);
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should allow access when user has required role', () => {
    const admin = {
      id: 'admin-123',
      email: 'admin@example.com',
      role: 'admin',
    };
    
    vi.mock('@/contexts/AuthContext', () => ({
      useAuth: () => ({
        user: admin,
        isLoading: false,
        isAuthenticated: true,
        hasRole: (role: string) => role === 'admin',
      }),
      AuthProvider: ({ children }: any) => children,
    }));

    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should deny access when user lacks required role', () => {
    const user = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user',
    };
    
    vi.mock('@/contexts/AuthContext', () => ({
      useAuth: () => ({
        user,
        isLoading: false,
        isAuthenticated: true,
        hasRole: (role: string) => role === 'user',
      }),
      AuthProvider: ({ children }: any) => children,
    }));

    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
