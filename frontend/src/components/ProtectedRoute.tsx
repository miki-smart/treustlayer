import { Navigate } from "react-router-dom";
import { useAuth, type UserRole } from "@/contexts/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";

const Spinner = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
  </div>
);

export default function ProtectedRoute({
  children,
  allow,
}: {
  children: React.ReactNode;
  allow?: UserRole[];
}) {
  const { isAuthenticated, isLoading, role } = useAuth();
  if (isLoading) return <Spinner />;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  if (allow && !allow.includes(role)) return <Navigate to="/dashboard" replace />;
  return <AppLayout>{children}</AppLayout>;
}
