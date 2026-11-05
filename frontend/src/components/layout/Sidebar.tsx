import { NavLink } from "react-router-dom";

import type { User, UserRole } from "../../types";

interface SidebarProps {
  user: User;
  onLogout: () => void;
}

interface NavigationItem {
  label: string;
  path: string;
  icon: string;
  roles: UserRole[];
  end?: boolean;
}

const navigation: {
  heading: string;
  items: NavigationItem[];
}[] = [
  {
    heading: "WORKSPACE",
    items: [
      {
        label: "Dashboard",
        path: "/",
        icon: "▦",
        roles: [
          "admin",
          "reviewer",
          "action_operator",
        ],
        end: true,
      },
      {
        label: "Invoices",
        path: "/invoices",
        icon: "▤",
        roles: ["admin", "reviewer"],
      },
      {
        label: "Upload invoice",
        path: "/invoices/upload",
        icon: "＋",
        roles: ["admin", "reviewer"],
      },
    ],
  },
  {
    heading: "OPERATIONS",
    items: [
      {
        label: "Exception Queue",
        path: "/exceptions",
        icon: "◈",
        roles: ["admin", "reviewer"],
      },
      {
        label: "Action center",
        path: "/actions",
        icon: "⇄",
        roles: ["admin", "action_operator"],
      },
      {
        label: "Workflow history",
        path: "/workflows",
        icon: "↗",
        roles: ["admin", "reviewer"],
      },
      {
        label: "Audit history",
        path: "/audit",
        icon: "≡",
        roles: ["admin", "action_operator"],
      },
    ],
  },
  {
    heading: "ACCOUNT",
    items: [
      {
        label: "My profile",
        path: "/profile",
        icon: "○",
        roles: [
          "admin",
          "reviewer",
          "action_operator",
        ],
      },
    ],
  },
];

export default function Sidebar({
  user,
  onLogout,
}: SidebarProps) {
  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          E
        </div>

        <div>
          <strong>ExceptionOps AI</strong>
          <span>Invoice Operations</span>
        </div>
      </div>

      <div className="sidebar-navigation">
        {navigation.map((group) => {
          const visibleItems = group.items.filter(
            (item) => item.roles.includes(user.role),
          );

          if (visibleItems.length === 0) {
            return null;
          }

          return (
            <div
              className="sidebar-group"
              key={group.heading}
            >
              <p className="sidebar-group-title">
                {group.heading}
              </p>

              {visibleItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.end}
                  className={({ isActive }) =>
                    isActive
                      ? "sidebar-link active"
                      : "sidebar-link"
                  }
                >
                  <span className="sidebar-link-icon">
                    {item.icon}
                  </span>

                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          );
        })}
      </div>

      <div className="sidebar-account">
        <div className="sidebar-account-avatar">
          {user.email.charAt(0).toUpperCase()}
        </div>

        <div className="sidebar-account-info">
          <strong>{user.email}</strong>

          <span>
            {user.role.replaceAll("_", " ")}
          </span>
        </div>

        <button
          className="sidebar-logout"
          type="button"
          onClick={onLogout}
          title="Sign out"
          aria-label="Sign out"
        >
          ↗
        </button>
      </div>
    </aside>
  );
}