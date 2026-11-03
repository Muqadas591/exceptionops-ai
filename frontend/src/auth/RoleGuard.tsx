import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

import type { UserRole } from "../types";

interface RoleGuardProps {
  allowedRoles: UserRole[];
  children: ReactNode;
}

export default function RoleGuard({
  allowedRoles,
  children,
}: RoleGuardProps) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}