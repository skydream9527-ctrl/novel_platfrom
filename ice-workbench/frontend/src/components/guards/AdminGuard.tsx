import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export function AdminGuard({
  children,
  superOnly = false,
}: {
  children: React.ReactNode;
  superOnly?: boolean;
}) {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;
  if (superOnly && user.auth_role !== "super_admin") {
    return <Navigate to="/admin" replace />;
  }
  if (user.auth_role !== "admin" && user.auth_role !== "super_admin") {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
