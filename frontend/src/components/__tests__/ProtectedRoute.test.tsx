import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const TestComponent = () => <div>Protected Content</div>;

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows spinner while loading", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      role: "user",
      login: async () => false,
      logout: () => {},
      isAuthenticated: false,
      isLoading: true,
      refreshUser: async () => {},
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <SidebarProvider>
          <Routes>
            <Route path="/app" element={<ProtectedRoute><TestComponent /></ProtectedRoute>} />
          </Routes>
        </SidebarProvider>
      </MemoryRouter>,
    );

    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("redirects when not authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      role: "user",
      login: async () => false,
      logout: () => {},
      isAuthenticated: false,
      isLoading: false,
      refreshUser: async () => {},
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <SidebarProvider>
          <Routes>
            <Route path="/app" element={<ProtectedRoute><TestComponent /></ProtectedRoute>} />
            <Route path="/" element={<div>Login</div>} />
          </Routes>
        </SidebarProvider>
      </MemoryRouter>,
    );

    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "a@b.com", role: "user", username: "u", full_name: null, phone_number: null, is_active: true, is_email_verified: true, created_at: "" } as any,
      role: "user",
      login: async () => false,
      logout: () => {},
      isAuthenticated: true,
      isLoading: false,
      refreshUser: async () => {},
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <SidebarProvider>
          <Routes>
            <Route path="/app" element={<ProtectedRoute><TestComponent /></ProtectedRoute>} />
          </Routes>
        </SidebarProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("allows access when role is in allow list", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "a@b.com", role: "admin", username: "a", full_name: null, phone_number: null, is_active: true, is_email_verified: true, created_at: "" } as any,
      role: "admin",
      login: async () => false,
      logout: () => {},
      isAuthenticated: true,
      isLoading: false,
      refreshUser: async () => {},
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <SidebarProvider>
          <Routes>
            <Route path="/app" element={<ProtectedRoute allow={["admin"]}><TestComponent /></ProtectedRoute>} />
          </Routes>
        </SidebarProvider>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("denies access when role is not in allow list", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: "1", email: "u@b.com", role: "user", username: "u", full_name: null, phone_number: null, is_active: true, is_email_verified: true, created_at: "" } as any,
      role: "user",
      login: async () => false,
      logout: () => {},
      isAuthenticated: true,
      isLoading: false,
      refreshUser: async () => {},
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <SidebarProvider>
          <Routes>
            <Route path="/app" element={<ProtectedRoute allow={["admin"]}><TestComponent /></ProtectedRoute>} />
            <Route path="/dashboard" element={<div>Dashboard Page</div>} />
          </Routes>
        </SidebarProvider>
      </MemoryRouter>,
    );

    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
  });
});
