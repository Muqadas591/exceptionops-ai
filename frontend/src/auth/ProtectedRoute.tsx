import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { useAuth } from "./AuthContext";

export default function ProtectedRoute() {
  const {
    authenticated,
    loading,
  } = useAuth();

  const location = useLocation();

  if (loading) {
    return (
      <div className="auth-loading">
        <div className="loading-spinner" />

        <p>Verifying your session...</p>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return <Outlet />;
}