import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import KYCQueuePage from '../KYCQueuePage';

const mockKYCSubmissions = [
  {
    id: 'kyc-1',
    user_id: 'user-1',
    status: 'pending',
    tier: 'tier_0',
    full_name: 'John Doe',
    date_of_birth: '1990-01-01',
    document_type: 'passport',
    document_number: 'AB123456',
    address: '123 Main St',
    id_front_url: 'uploads/id_front.jpg',
    id_back_url: null,
    utility_bill_url: 'uploads/utility.jpg',
    face_image_url: 'uploads/face.jpg',
    overall_confidence: 0.95,
    risk_score: 15,
    rejection_reason: null,
    reviewer_id: null,
    submitted_at: new Date().toISOString(),
    reviewed_at: null,
  },
];

describe('KYCQueuePage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <KYCQueuePage />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should render page title', () => {
    renderPage();
    expect(screen.getByText(/KYC Review Queue/i)).toBeInTheDocument();
  });

  it('should render status tabs', () => {
    renderPage();
    expect(screen.getByText(/Pending/i)).toBeInTheDocument();
    expect(screen.getByText(/In Review/i)).toBeInTheDocument();
    expect(screen.getByText(/Approved/i)).toBeInTheDocument();
    expect(screen.getByText(/Rejected/i)).toBeInTheDocument();
  });

  it('should display KYC submissions', async () => {
    vi.mock('@/services/api', () => ({
      kycApi: {
        listQueue: vi.fn().mockResolvedValue(mockKYCSubmissions),
      },
    }));

    renderPage();
    
    const name = await screen.findByText('John Doe');
    expect(name).toBeInTheDocument();
  });

  it('should show review button', async () => {
    vi.mock('@/services/api', () => ({
      kycApi: {
        listQueue: vi.fn().mockResolvedValue(mockKYCSubmissions),
      },
    }));

    renderPage();
    
    const reviewButton = await screen.findByText(/Review Details/i);
    expect(reviewButton).toBeInTheDocument();
  });

  it('should open review dialog on button click', async () => {
    vi.mock('@/services/api', () => ({
      kycApi: {
        listQueue: vi.fn().mockResolvedValue(mockKYCSubmissions),
      },
    }));

    const user = userEvent.setup();
    renderPage();
    
    const reviewButton = await screen.findByText(/Review Details/i);
    await user.click(reviewButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Review KYC Submission/i)).toBeInTheDocument();
    });
  });
});
