import type { User } from "../../types";

interface TopbarProps {
  user: User;
}

export default function Topbar({
  user,
}: TopbarProps) {
  return (
    <header className="app-topbar">
      <div className="topbar-context">
        <span>ExceptionOps AI</span>

        <span className="topbar-separator">/</span>

        <strong>Operations workspace</strong>
      </div>

      <div className="topbar-user">
        <span className="topbar-status-dot" />

        <span className="topbar-user-email">
          {user.email}
        </span>

        <span className="topbar-role">
          {user.role.replaceAll("_", " ")}
        </span>
      </div>
    </header>
  );
}