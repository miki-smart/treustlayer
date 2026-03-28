import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "../AppSidebar";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

function renderSidebar(role: string) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: "u1", email: "x@y.com", role, username: "u", full_name: null, phone_number: null, is_active: true, is_email_verified: true, created_at: "" } as any,
    role: role as any,
    login: async () => null,
    logout: () => {},
    isAuthenticated: true,
    isLoading: false,
    refreshUser: async () => {},
  });

  return render(
    <BrowserRouter>
      <SidebarProvider>
        <AppSidebar />
      </SidebarProvider>
    </BrowserRouter>,
  );
}

describe("AppSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Apps hub for user role (no separate consent/sessions)", () => {
    renderSidebar("user");
    expect(screen.getByText(/^Apps$/i)).toBeInTheDocument();
    expect(screen.getByText(/eKYC/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Consent$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Connected apps/i)).not.toBeInTheDocument();
  });

  it("shows admin ops and developers for admin (no consumer menus)", () => {
    renderSidebar("admin");
    expect(screen.getByText(/Admin dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/KYC queue/i)).toBeInTheDocument();
    expect(screen.getByText(/App approvals/i)).toBeInTheDocument();
    expect(screen.getByText(/Audit logs/i)).toBeInTheDocument();
    expect(screen.getByText(/App directory/i)).toBeInTheDocument();
    expect(screen.queryByText(/^eKYC$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Connected apps/i)).not.toBeInTheDocument();
  });

  it("shows only verification for kyc_approver", () => {
    renderSidebar("kyc_approver");
    expect(screen.getByText(/KYC queue/i)).toBeInTheDocument();
    expect(screen.queryByText(/eKYC/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Apps$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Admin dashboard/i)).not.toBeInTheDocument();
  });

  it("shows only developers for app_owner", () => {
    renderSidebar("app_owner");
    expect(screen.getByText(/My OAuth clients/i)).toBeInTheDocument();
    expect(screen.getByText(/App directory/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Apps$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^eKYC$/i)).not.toBeInTheDocument();
  });

  it("hides admin items from regular user", () => {
    renderSidebar("user");
    expect(screen.queryByText(/Admin dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/App approvals/i)).not.toBeInTheDocument();
  });

  it("does not show KYC queue to app_owner", () => {
    renderSidebar("app_owner");
    expect(screen.queryByText(/KYC queue/i)).not.toBeInTheDocument();
  });
});
