import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import MyAppsPage from "../MyAppsPage";

const hoisted = vi.hoisted(() => ({
  mockApps: [
    {
      id: "app-1",
      name: "My Test App",
      client_id: "app_abc123",
      owner_id: "user-123",
      allowed_scopes: ["openid", "profile", "email"],
      redirect_uris: ["http://localhost:3000/callback"],
      description: "Test application",
      category: "general",
      is_active: true,
      is_approved: true,
      is_public: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
}));

vi.mock("@/services/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/services/api")>();
  return {
    ...actual,
    appsApi: {
      ...actual.appsApi,
      mine: vi.fn().mockResolvedValue(hoisted.mockApps),
    },
  };
});

describe("MyAppsPage", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  beforeEach(() => {
    queryClient.clear();
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <MyAppsPage />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  it("should render page title", () => {
    renderPage();
    expect(screen.getByText(/My Applications/i)).toBeInTheDocument();
  });

  it("should show register button", () => {
    renderPage();
    expect(screen.getByText(/Register New App/i)).toBeInTheDocument();
  });

  it("should display apps list", async () => {
    renderPage();
    expect(await screen.findByText("My Test App")).toBeInTheDocument();
  });

  it("should show client ID", async () => {
    renderPage();
    expect(await screen.findByText("app_abc123")).toBeInTheDocument();
  });

  it("should show approved badge", async () => {
    renderPage();
    expect(await screen.findByText(/Approved/i)).toBeInTheDocument();
  });

  it("should open register dialog on button click", async () => {
    const user = userEvent.setup();
    renderPage();
    const registerButton = screen.getByText(/Register New App/i);
    await user.click(registerButton);
    await waitFor(() => {
      expect(screen.getByText(/Register New Application/i)).toBeInTheDocument();
    });
  });
});
