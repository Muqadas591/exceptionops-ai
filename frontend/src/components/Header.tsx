import { useAuth } from "../auth/AuthContext";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-mark">E</div>
        <div>
          <h1>ExceptionOps</h1>
          <p>Invoice Operations Platform</p>
        </div>
      </div>

      <div className="token-controls">
        <span>
          {user ? `${user.email} · ${user.role.replaceAll("_", " ")}` : ""}
        </span>
        <button className="button button-secondary" onClick={logout}>
          Sign out
        </button>
      </div>
    </header>
  );
}