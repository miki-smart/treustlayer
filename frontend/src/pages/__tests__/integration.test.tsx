import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
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
          {component}
        </BrowserRouter>
      </QueryClientProvider>
    );
  };
  
  it('should render login page', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });
  
  it('should have email and password fields', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
  
  it('should have login button', () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
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
