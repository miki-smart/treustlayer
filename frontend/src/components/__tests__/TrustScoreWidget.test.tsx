import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TrustScoreWidget } from "../TrustScoreWidget";

const hoisted = vi.hoisted(() => ({
  mockTrustProfile: {
    user_id: "user-123",
    trust_score: 85,
    risk_level: "low",
    email_verified: true,
    phone_verified: true,
    kyc_tier: 2,
    face_verified: true,
    voice_verified: true,
    digital_identity_active: true,
    account_age_days: 180,
    last_calculated_at: new Date().toISOString(),
  },
}));

vi.mock("@/services/api", () => ({
  trustApi: {
    getProfile: vi.fn().mockResolvedValue(hoisted.mockTrustProfile),
    getUserProfile: vi.fn().mockResolvedValue(hoisted.mockTrustProfile),
  },
}));

describe("TrustScoreWidget", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  beforeEach(() => {
    queryClient.clear();
  });

  const renderWidget = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <TrustScoreWidget {...props} />
      </QueryClientProvider>,
    );
  };

  it("should render loading state", () => {
    renderWidget();
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("should display trust score", async () => {
    renderWidget();
    expect(await screen.findByText("85")).toBeInTheDocument();
  });

  it("should show low risk badge for high score", async () => {
    renderWidget();
    expect(await screen.findByText(/LOW RISK/i)).toBeInTheDocument();
  });

  it("should show verification checkmarks", async () => {
    renderWidget();
    expect(await screen.findByText(/Email Verified/i)).toBeInTheDocument();
  });

  it("should show refresh button when showRefresh is true", async () => {
    renderWidget({ showRefresh: true });
    expect(await screen.findByText(/Recalculate/i)).toBeInTheDocument();
  });
});
