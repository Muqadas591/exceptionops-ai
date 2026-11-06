import {
  Outlet,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../../auth/AuthContext";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout() {
  const {
    user,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  function handleLogout() {
    logout();

    navigate("/login", {
      replace: true,
    });
  }

  return (
    <div className="application-shell">
      <Sidebar
        user={user}
        onLogout={handleLogout}
      />

      <div className="application-content">
        <Topbar user={user} />

        <div className="application-page-content">
          <Outlet />
        </div>

        <footer className="application-footer">
          <span>ExceptionOps AI</span>

          <span>
            AI-assisted processing · Human oversight ·
            Controlled actions
          </span>
        </footer>
      </div>
    </div>
  );
}