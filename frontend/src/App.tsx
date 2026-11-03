import {
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";

import LoginPage from "./auth/LoginPage";
import ProtectedRoute from "./auth/ProtectedRoute";

function DashboardPage() {
  const { user } = useAuth();

  return (
    <main className="dashboard-page">
      <div className="dashboard-welcome">
        <div>
          <p className="eyebrow">
            OPERATIONS OVERVIEW
          </p>

          <h1>Invoice exception management</h1>

          <p>
            Welcome, {user?.email}. Your workspace
            brings invoice processing, business validation,
            human review and controlled actions together.
          </p>
        </div>

        <span className="role-label">
          {user?.role.replaceAll("_", " ")}
        </span>
      </div>

      <section className="purpose-card">
        <p className="eyebrow">
          WHAT EXCEPTIONOPS AI DOES
        </p>

        <h2>
          Turn incoming invoices into controlled,
          reviewable business workflows.
        </h2>

        <p>
          ExceptionOps AI receives invoice documents,
          extracts relevant information, evaluates
          business rules, identifies discrepancies,
          and routes exceptions for human review.
          Authorized operators can then execute
          controlled actions and inspect recorded outcomes.
        </p>
      </section>

      <section className="pipeline-section">
        <div className="section-heading">
          <div>
            <h2>How the platform works</h2>

            <p>
              The operational lifecycle of an invoice.
            </p>
          </div>
        </div>

        <div className="pipeline-grid">
          {[
            {
              number: "01",
              title: "Invoice intake",
              description:
                "Receive and store invoice documents.",
            },
            {
              number: "02",
              title: "Data extraction",
              description:
                "Extract invoice fields and supporting evidence.",
            },
            {
              number: "03",
              title: "Business validation",
              description:
                "Evaluate business rules and identify discrepancies.",
            },
            {
              number: "04",
              title: "Exception detection",
              description:
                "Identify cases that need further attention.",
            },
            {
              number: "05",
              title: "Human review",
              description:
                "Assign reviewers and record decisions.",
            },
            {
              number: "06",
              title: "Controlled action",
              description:
                "Execute authorized simulations and record outcomes.",
            },
          ].map((step) => (
            <article
              className="pipeline-card"
              key={step.number}
            >
              <span>{step.number}</span>

              <h3>{step.title}</h3>

              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="dashboard-note">
        <strong>Operational integrity</strong>

        <p>
          AI-assisted extraction and business-rule
          evaluation support the process. Human
          authorization remains part of exception
          resolution. Connector actions in this
          portfolio implementation are simulations
          and drafts.
        </p>
      </section>
    </main>
  );
}

function ApplicationLayout() {
  const {
    user,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="application-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-symbol">E</div>

          <div>
            <strong>ExceptionOps AI</strong>
            <span>Invoice Operations</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p>WORKSPACE</p>

          <NavLink to="/" end>
            Overview
          </NavLink>

          <NavLink to="/invoices">
            Invoices
          </NavLink>

          <NavLink to="/invoices/upload">
            Upload invoice
          </NavLink>
        </div>

        <div className="sidebar-section">
          <p>OPERATIONS</p>

          <NavLink to="/exceptions">
            Exception queue
          </NavLink>

          {(
            user?.role === "admin" ||
            user?.role === "action_operator"
          ) && (
            <NavLink to="/actions">
              Action center
            </NavLink>
          )}

          <NavLink to="/audit">
            Audit history
          </NavLink>
        </div>

        <div className="sidebar-section">
          <p>ACCOUNT</p>

          <NavLink to="/profile">
            My profile
          </NavLink>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">
            {user?.email.charAt(0).toUpperCase()}
          </div>

          <div className="user-information">
            <strong>{user?.email}</strong>

            <span>
              {user?.role.replaceAll("_", " ")}
            </span>
          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
            title="Sign out"
          >
            ↗
          </button>
        </div>
      </aside>

      <div className="application-main">
        <header className="topbar">
          <div>
            <span>ExceptionOps AI</span>
            <span className="topbar-divider">/</span>
            <span>Operations workspace</span>
          </div>

          <div className="topbar-user">
            <span className="online-indicator" />
            {user?.email}
          </div>
        </header>

        <Outlet />
      </div>
    </div>
  );
}

function ComingSoonPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="dashboard-page">
      <p className="eyebrow">OPERATIONS</p>

      <h1>{title}</h1>

      <p>{description}</p>

      <div className="purpose-card">
        This screen will be connected to the existing
        backend functionality in the next frontend phase.
      </div>
    </main>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<ApplicationLayout />}>
          <Route path="/" element={<DashboardPage />} />

          <Route
            path="/invoices"
            element={
              <ComingSoonPage
                title="Invoice management"
                description="Manage uploaded invoice documents and inspect their processing status."
              />
            }
          />

          <Route
            path="/invoices/upload"
            element={
              <ComingSoonPage
                title="Upload invoice"
                description="Upload a supported invoice document to begin processing."
              />
            }
          />

          <Route
            path="/exceptions"
            element={
              <ComingSoonPage
                title="Exception queue"
                description="Investigate invoice discrepancies and manage human reviews."
              />
            }
          />

          <Route
            path="/actions"
            element={
              <ComingSoonPage
                title="Action center"
                description="Inspect authorized connector actions and recovery operations."
              />
            }
          />

          <Route
            path="/audit"
            element={
              <ComingSoonPage
                title="Audit history"
                description="Inspect recorded operational events and action outcomes."
              />
            }
          />

          <Route
            path="/profile"
            element={
              <ComingSoonPage
                title="My profile"
                description="View your account identity and application role."
              />
            }
          />
        </Route>
      </Route>

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}