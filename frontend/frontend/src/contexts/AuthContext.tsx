import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { authApi, tokenStore, UserResponse } from "@/services/api";

export type UserRole = "admin" | "user" | "kyc_approver" | "app_owner";

export interface AppUser extends UserResponse {
  name: string;
  avatar?: string;
}

interface AuthContextType {
  user: AppUser | null;
  role: UserRole;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function toAppUser(u: UserResponse): AppUser {
  return { ...u, name: u.full_name || u.username, avatar: undefined };
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!tokenStore.get()) return;
    try {
      const me = await authApi.me();
      setUser(toAppUser(me));
    } catch {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const res = await authApi.login(username, password);
      tokenStore.set(res.access_token);
      if (res.refresh_token) tokenStore.setRefresh(res.refresh_token);
      const me = await authApi.me();
      setUser(toAppUser(me));
      return true;
    } catch (err) {
      console.error("Login failed:", err);
      return false;
    }
  };

  const logout = () => {
    const rt = tokenStore.getRefresh();
    if (rt) authApi.logout(rt).catch(() => {});
    tokenStore.clear();
    setUser(null);
  };

  // Role is always derived from the server response — never mutable by the client
  const role = (user?.role as UserRole) ?? "user";

  return (
    <AuthContext.Provider value={{
      user,
      role,
      login,
      logout,
      isAuthenticated: !!user,
      isLoading,
      refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
