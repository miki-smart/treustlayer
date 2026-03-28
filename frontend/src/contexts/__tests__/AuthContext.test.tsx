import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "../AuthContext";

const fullUser = {
  id: "user-123",
  email: "test@example.com",
  username: "testuser",
  role: "user",
  full_name: null as string | null,
  phone_number: null as string | null,
  is_active: true,
  is_email_verified: true,
  created_at: new Date().toISOString(),
};

const TestComponent = () => {
  const { user, isLoading, isAuthenticated } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? "Loading" : "Not Loading"}</div>
      <div data-testid="authenticated">{isAuthenticated ? "Authenticated" : "Not Authenticated"}</div>
      <div data-testid="user">{user ? user.email : "No User"}</div>
    </div>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("should provide initial unauthenticated state", () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    expect(screen.getByTestId("authenticated")).toHaveTextContent("Not Authenticated");
    expect(screen.getByTestId("user")).toHaveTextContent("No User");
  });

  it("should load user from localStorage if access_token exists", async () => {
    localStorage.setItem("access_token", "fake-token");

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fullUser,
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("Authenticated");
    });

    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
  });

  it("should handle login", async () => {
    const LoginComponent = () => {
      const { login } = useAuth();
      return (
        <button type="button" onClick={() => login("test@example.com", "password")}>
          Login
        </button>
      );
    };

    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: "token",
          token_type: "Bearer",
          expires_in: 900,
          user_id: fullUser.id,
          username: fullUser.username,
          role: fullUser.role,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => fullUser,
      });

    render(
      <AuthProvider>
        <LoginComponent />
        <TestComponent />
      </AuthProvider>,
    );

    screen.getByText("Login").click();

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("Authenticated");
    });
  });

  it("should handle logout", async () => {
    localStorage.setItem("access_token", "fake-token");

    const LogoutComponent = () => {
      const { logout } = useAuth();
      return (
        <button type="button" onClick={logout}>
          Logout
        </button>
      );
    };

    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });

    render(
      <AuthProvider>
        <LogoutComponent />
        <TestComponent />
      </AuthProvider>,
    );

    screen.getByText("Logout").click();

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("Not Authenticated");
    });

    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("should expose role for RBAC checks", async () => {
    localStorage.setItem("access_token", "fake-token");

    const adminUser = { ...fullUser, id: "admin-123", email: "admin@example.com", username: "admin", role: "admin" };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => adminUser,
    });

    const RoleComponent = () => {
      const { role } = useAuth();
      return (
        <div>
          <div data-testid="is-admin">{role === "admin" ? "Yes" : "No"}</div>
          <div data-testid="is-user">{role === "user" ? "Yes" : "No"}</div>
        </div>
      );
    };

    render(
      <AuthProvider>
        <RoleComponent />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("is-admin")).toHaveTextContent("Yes");
    });
    expect(screen.getByTestId("is-user")).toHaveTextContent("No");
  });
});
