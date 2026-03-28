import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import EKYCPage from "./pages/EKYCPage";
import BiometricPage from "./pages/BiometricPage";
import IdentityPage from "./pages/IdentityPage";
import AppMarketplacePage from "./pages/AppMarketplacePage";
import SettingsPage from "./pages/SettingsPage";
import KYCQueuePage from "./pages/KYCQueuePage";
import MyAppsPage from "./pages/MyAppsPage";
import AppApprovalPage from "./pages/AppApprovalPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

const Spinner = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
  </div>
);

function LoginRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <Spinner />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <LoginPage />;
}

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<LoginRoute />} />

    <Route path="/dashboard"  element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
    <Route path="/settings"   element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />

    {/* End-user identity & integrations (role: user) */}
    <Route path="/ekyc"       element={<ProtectedRoute allow={["user"]}><EKYCPage /></ProtectedRoute>} />
    <Route path="/biometric"  element={<ProtectedRoute allow={["user"]}><BiometricPage /></ProtectedRoute>} />
    <Route path="/identity"   element={<ProtectedRoute allow={["user"]}><IdentityPage /></ProtectedRoute>} />
    {/* Legacy paths → unified Apps hub for end users */}
    <Route path="/connected-apps" element={<Navigate to="/apps?tab=connections" replace />} />
    <Route path="/consent" element={<Navigate to="/apps?tab=connections" replace />} />
    <Route path="/sessions" element={<Navigate to="/apps?tab=connections" replace />} />

    {/* Admin: all apps; app_owner: own; user: marketplace + my connections */}
    <Route path="/apps" element={
      <ProtectedRoute allow={["admin", "app_owner", "user"]}>
        <AppMarketplacePage />
      </ProtectedRoute>
    } />
    
    <Route path="/my-apps" element={
      <ProtectedRoute allow={["admin", "app_owner"]}>
        <MyAppsPage />
      </ProtectedRoute>
    } />
    
    {/* Admin Only */}
    <Route path="/admin" element={
      <ProtectedRoute allow={["admin"]}>
        <AdminDashboardPage />
      </ProtectedRoute>
    } />
    
    <Route path="/app-approvals" element={
      <ProtectedRoute allow={["admin"]}>
        <AppApprovalPage />
      </ProtectedRoute>
    } />
    
    <Route path="/audit-logs" element={
      <ProtectedRoute allow={["admin"]}>
        <AuditLogsPage />
      </ProtectedRoute>
    } />

    {/* KYC Approver + Admin */}
    <Route path="/kyc-queue" element={
      <ProtectedRoute allow={["admin", "kyc_approver"]}>
        <KYCQueuePage />
      </ProtectedRoute>
    } />

    <Route path="*" element={<NotFound />} />
  </Routes>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
