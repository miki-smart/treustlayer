import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { ReactNode } from 'react';

const TestComponent = () => {
  const { user, isLoading, isAuthenticated } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</div>
      <div data-testid="user">{user ? user.email : 'No User'}</div>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should provide initial unauthenticated state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    expect(screen.getByTestId('authenticated')).toHaveTextContent('Not Authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('No User');
  });

  it('should load user from localStorage if token exists', async () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
    };
    
    localStorage.setItem('token', 'fake-token');
    localStorage.setItem('user', JSON.stringify(mockUser));
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    });
    
    expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
  });

  it('should handle login', async () => {
    const mockUser = {
      id: 'user-123',
      email: 'test@example.com',
      username: 'testuser',
      role: 'user',
    };
    
    const LoginComponent = () => {
      const { login } = useAuth();
      
      return (
        <button onClick={() => login('test@example.com', 'password')}>
          Login
        </button>
      );
    };
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: 'token',
        user: mockUser,
      }),
    });
    
    render(
      <AuthProvider>
        <LoginComponent />
        <TestComponent />
      </AuthProvider>
    );
    
    const loginButton = screen.getByText('Login');
    loginButton.click();
    
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    });
  });

  it('should handle logout', async () => {
    localStorage.setItem('token', 'fake-token');
    localStorage.setItem('user', JSON.stringify({ email: 'test@example.com' }));
    
    const LogoutComponent = () => {
      const { logout } = useAuth();
      
      return <button onClick={logout}>Logout</button>;
    };
    
    render(
      <AuthProvider>
        <LogoutComponent />
        <TestComponent />
      </AuthProvider>
    );
    
    const logoutButton = screen.getByText('Logout');
    logoutButton.click();
    
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Not Authenticated');
    });
    
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('should check user role', () => {
    const mockUser = {
      id: 'admin-123',
      email: 'admin@example.com',
      username: 'admin',
      role: 'admin',
    };
    
    localStorage.setItem('token', 'fake-token');
    localStorage.setItem('user', JSON.stringify(mockUser));
    
    const RoleComponent = () => {
      const { hasRole } = useAuth();
      
      return (
        <div>
          <div data-testid="is-admin">{hasRole('admin') ? 'Yes' : 'No'}</div>
          <div data-testid="is-user">{hasRole('user') ? 'Yes' : 'No'}</div>
        </div>
      );
    };
    
    render(
      <AuthProvider>
        <RoleComponent />
      </AuthProvider>
    );
    
    expect(screen.getByTestId('is-admin')).toHaveTextContent('Yes');
    expect(screen.getByTestId('is-user')).toHaveTextContent('No');
  });
});
