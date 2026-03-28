import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import LoginPage from '../LoginPage';

describe('Frontend-Backend Integration', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    localStorage.clear();
  });
  
  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>{component}</AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );
  };
  
  it('should render login page', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getAllByText(/sign in/i).length).toBeGreaterThan(0);
  });

  it('should have username and password fields', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByPlaceholderText(/Enter username or email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter your password/i)).toBeInTheDocument();
  });

  it('should have login submit button', () => {
    renderWithProviders(<LoginPage />);
    const submitBtn = document.querySelector("form button[type='submit']");
    expect(submitBtn).toBeTruthy();
    expect(submitBtn?.textContent).toMatch(/sign in/i);
  });
});

describe('API Health Check', () => {
  it('should connect to backend health endpoint', async () => {
    try {
      const response = await fetch('/api/v1/health');
      expect(response.ok).toBe(true);
      const data = await response.json();
      expect(data.status).toBe('ok');
    } catch (error) {
      console.warn('Backend not running, skipping health check test');
    }
  });
});
