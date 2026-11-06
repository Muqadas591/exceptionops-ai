import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

import { api } from "../api";

import type {
  ActionExecution,
  Document,
  HealthResponse,
  HumanReview,
  ReadinessResponse,
} from "../types";

import MetricCard from "../components/dashboard/MetricCard";
import ServiceHealthCard from "../components/dashboard/ServiceHealthCard";
import WorkflowOverview from "../components/dashboard/WorkflowOverview";

type ServiceStatus =
  | "healthy"
  | "unavailable"
  | "checking";

interface DashboardState {
  documents: Document[];
  reviews: HumanReview[];
  recoveryActions: ActionExecution[];

  pendingReviews: number | null;
  correctionRequested: number | null;
  approvedReviews: number | null;
  totalReviews: number | null;

  health: HealthResponse | null;
  readiness: ReadinessResponse | null;

  applicationStatus: ServiceStatus;
  databaseStatus: ServiceStatus;

  loading: boolean;
  error: string;
}

const initialState: DashboardState = {
  documents: [],
  reviews: [],
  recoveryActions: [],

  pendingReviews: null,
  correctionRequested: null,
  approvedReviews: null,
  totalReviews: null,

  health: null,
  readiness: null,

  applicationStatus: "checking",
  databaseStatus: "checking",

  loading: true,
  error: "",
};

function formatDate(value: string): string {
  return new Date(value).toLocaleString(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function statusClass(status: string): string {
  switch (status.toLowerCase()) {
    case "approved":
    case "succeeded":
    case "resolved":
    case "ready":
    case "received":
      return "status-success";

    case "pending":
    case "needs_review":
    case "correction_requested":
    case "uncertain":
      return "status-warning";

    case "failed":
    case "rejected":
    case "blocked":
      return "status-danger";

    default:
      return "status-neutral";
  }
}

export default function DashboardPage() {
  const { user } = useAuth();

  const [state, setState] =
    useState<DashboardState>(initialState);

  const isReviewer =
    user?.role === "admin" ||
    user?.role === "reviewer";

  const isActionOperator =
    user?.role === "admin" ||
    user?.role === "action_operator";

  const loadDashboard = useCallback(async () => {
    if (!user) {
      return;
    }

    setState((current) => ({
      ...current,
      loading: true,
      error: "",
    }));

    const next: DashboardState = {
      ...initialState,
      loading: false,
    };

    // ---------------------------------
    // APPLICATION HEALTH
    // ---------------------------------

    const healthResult = await Promise.allSettled([
      api.getHealth(),
      api.getReadiness(),
    ]);

    if (healthResult[0].status === "fulfilled") {
      next.health = healthResult[0].value;
      next.applicationStatus = "healthy";
    } else {
      next.applicationStatus = "unavailable";
    }

    if (healthResult[1].status === "fulfilled") {
      next.readiness = healthResult[1].value;
      next.databaseStatus = "healthy";
    } else {
      next.databaseStatus = "unavailable";
    }

    // ---------------------------------
    // DOCUMENTS AND REVIEWS
    // Admin and reviewer roles only.
    // ---------------------------------

    if (isReviewer) {
      const documentResult = await Promise.allSettled([
        api.getDocuments(100, 0),
        api.getQueuePage(undefined, undefined, 8, 0),
        api.getReviewCount("pending"),
        api.getReviewCount("correction_requested"),
        api.getReviewCount("approved"),
      ]);

      if (documentResult[0].status === "fulfilled") {
        next.documents = documentResult[0].value;
      }

      if (documentResult[1].status === "fulfilled") {
        next.reviews = documentResult[1].value.items;
        next.totalReviews = documentResult[1].value.total;
      }

      if (documentResult[2].status === "fulfilled") {
        next.pendingReviews = documentResult[2].value;
      }

      if (documentResult[3].status === "fulfilled") {
        next.correctionRequested =
          documentResult[3].value;
      }

      if (documentResult[4].status === "fulfilled") {
        next.approvedReviews = documentResult[4].value;
      }

      const documentFailed =
        documentResult[0].status === "rejected";

      const queueFailed =
        documentResult[1].status === "rejected";

      if (documentFailed || queueFailed) {
        next.error =
          "Some operational data could not be loaded. Check the backend and your account permissions.";
      }
    }

    // ---------------------------------
    // ACTION RECOVERY
    // Admin and action_operator roles.
    // ---------------------------------

    if (isActionOperator) {
      const recoveryResult =
        await Promise.allSettled([
          api.getRecoveryQueue(100, 0),
        ]);

      if (recoveryResult[0].status === "fulfilled") {
        next.recoveryActions =
          recoveryResult[0].value;
      } else if (!next.error) {
        next.error =
          "The action recovery queue could not be loaded.";
      }
    }

    setState(next);
  }, [user, isReviewer, isActionOperator]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  if (!user) {
    return null;
  }

  const pendingReviewCount =
    (state.pendingReviews ?? 0) +
    (state.correctionRequested ?? 0);

  const recoveryCount =
    state.recoveryActions.length;

  const recentDocuments =
    state.documents.slice(0, 6);

  const recentReviews =
    state.reviews.slice(0, 6);

  return (
    <main className="dashboard-page">
      {/* PAGE INTRODUCTION */}

      <section className="dashboard-introduction">
        <div>
          <p className="eyebrow">
            OPERATIONS OVERVIEW
          </p>

          <h1>Invoice operations dashboard</h1>

          <p className="dashboard-description">
            Welcome back, {user.email}. Monitor invoice
            intake, business validation, exception reviews
            and controlled action recovery from one workspace.
          </p>
        </div>

        <button
          className="button button-secondary"
          onClick={() => void loadDashboard()}
          disabled={state.loading}
        >
          {state.loading ? "Refreshing..." : "↻ Refresh"}
        </button>
      </section>

      {state.error && (
        <div className="notice notice-error">
          {state.error}
        </div>
      )}

      {/* PURPOSE */}

      <section className="dashboard-purpose">
        <div className="dashboard-purpose-content">
          <p className="eyebrow">
            INTELLIGENT INVOICE EXCEPTION MANAGEMENT
          </p>

          <h2>
            From incoming invoices to controlled
            business resolution.
          </h2>

          <p>
            ExceptionOps AI helps operations teams
            process invoice documents, extract important
            information, evaluate business rules, identify
            discrepancies, and route unresolved cases
            for human review.
          </p>

          <p>
            Authorized users can record decisions and
            execute controlled connector simulations,
            while operational events remain traceable.
          </p>

          <div className="dashboard-purpose-actions">
            {isReviewer && (
              <Link
                to="/invoices/upload"
                className="button button-primary"
              >
                Upload an invoice
              </Link>
            )}

            {isReviewer && (
              <Link
                to="/exceptions"
                className="button button-secondary"
              >
                Open exception queue
              </Link>
            )}
          </div>
        </div>

        <div className="dashboard-purpose-visual">
          <div className="purpose-visual-icon">E</div>

          <strong>ExceptionOps AI</strong>

          <span>
            AI-assisted operations
          </span>

          <div className="purpose-visual-divider" />

          <span>Extraction</span>
          <span>Validation</span>
          <span>Human review</span>
          <span>Controlled actions</span>
        </div>
      </section>

      {/* OPERATIONAL METRICS */}

      <section className="dashboard-section">
        <div className="dashboard-section-heading">
          <div>
            <h2>Operational snapshot</h2>

            <p>
              Values are calculated from backend records
              available to your account.
            </p>
          </div>
        </div>

        <div className="metric-grid">
          {isReviewer && (
            <MetricCard
              label="Documents loaded"
              value={state.documents.length}
              description="Latest page, up to 100 records"
              icon="▤"
              tone="blue"
              loading={state.loading}
            />
          )}

          {isReviewer && (
            <MetricCard
              label="Pending reviews"
              value={pendingReviewCount}
              description="Pending and correction requested"
              icon="◈"
              tone="amber"
              loading={state.loading}
            />
          )}

          {isReviewer && (
            <MetricCard
              label="Approved reviews"
              value={state.approvedReviews ?? "—"}
              description="Matching records across the queue"
              icon="✓"
              tone="green"
              loading={state.loading}
            />
          )}

          {isActionOperator && (
            <MetricCard
              label="Recovery items loaded"
              value={recoveryCount}
              description="Latest recovery page, up to 100"
              icon="↻"
              tone="red"
              loading={state.loading}
            />
          )}
        </div>

        {isReviewer && state.totalReviews !== null && (
          <p className="dashboard-data-note">
            Review queue total: {state.totalReviews}.
            Review counts use the backend's
            X-Total-Count pagination header.
          </p>
        )}

        {isReviewer && state.documents.length === 100 && (
          <p className="dashboard-data-note">
            The document list is limited to the latest
            100 records on this dashboard. It is not
            presented as the database-wide total.
          </p>
        )}
      </section>

      {/* RECENT DOCUMENTS */}

      {isReviewer && (
        <section className="panel dashboard-data-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent invoice documents</h3>

              <p className="muted">
                Latest documents returned by the backend.
              </p>
            </div>

            <Link
              to="/invoices"
              className="text-link"
            >
              View invoices →
            </Link>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Document</th>
                  <th>File size</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {recentDocuments.map((document) => (
                  <tr key={document.id}>
                    <td>
                      <div className="document-table-name">
                        <strong>
                          {document.original_filename}
                        </strong>

                        <span>
                          Document #{document.id}
                        </span>
                      </div>
                    </td>

                    <td>
                      {formatFileSize(
                        document.file_size_bytes,
                      )}
                    </td>

                    <td>
                      <span
                        className={`status-badge ${statusClass(
                          document.status,
                        )}`}
                      >
                        {document.status.replaceAll("_", " ")}
                      </span>
                    </td>

                    <td>
                      {formatDate(document.created_at)}
                    </td>

                    <td>
                      <Link
                        to={`/invoices/${document.id}`}
                        className="button button-small button-secondary"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}

                {!state.loading &&
                  recentDocuments.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="empty-cell"
                      >
                        No documents have been uploaded yet.
                        Use Upload Invoice to begin.
                      </td>
                    </tr>
                  )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* RECENT REVIEWS */}

      {isReviewer && (
        <section className="panel dashboard-data-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent exception activity</h3>

              <p className="muted">
                Latest review records returned by the backend.
              </p>
            </div>

            <Link
              to="/exceptions"
              className="text-link"
            >
              View exception queue →
            </Link>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Review</th>
                  <th>Workflow</th>
                  <th>Assigned to</th>
                  <th>Status</th>
                  <th>Last updated</th>
                </tr>
              </thead>

              <tbody>
                {recentReviews.map((review) => (
                  <tr key={review.id}>
                    <td>
                      <strong>#{review.id}</strong>
                    </td>

                    <td>
                      #{review.workflow_run_id}
                    </td>

                    <td>
                      {review.assigned_to || "Unassigned"}
                    </td>

                    <td>
                      <span
                        className={`status-badge ${statusClass(
                          review.status,
                        )}`}
                      >
                        {review.status.replaceAll("_", " ")}
                      </span>
                    </td>

                    <td>
                      {formatDate(review.updated_at)}
                    </td>
                  </tr>
                ))}

                {!state.loading &&
                  recentReviews.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="empty-cell"
                      >
                        No review records are available.
                      </td>
                    </tr>
                  )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ACTION RECOVERY */}

      {isActionOperator && (
        <section className="panel dashboard-data-panel">
          <div className="panel-heading">
            <div>
              <h3>Action recovery overview</h3>

              <p className="muted">
                Records returned by the action recovery endpoint.
              </p>
            </div>

            <Link
              to="/actions"
              className="text-link"
            >
              Open action center →
            </Link>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Review</th>
                  <th>Action type</th>
                  <th>Status</th>
                  <th>Attempts</th>
                </tr>
              </thead>

              <tbody>
                {state.recoveryActions.map((action) => (
                  <tr key={action.id}>
                    <td>
                      <strong>#{action.id}</strong>
                    </td>

                    <td>
                      #{action.review_id}
                    </td>

                    <td>
                      {action.action_type.replaceAll("_", " ")}
                    </td>

                    <td>
                      <span
                        className={`status-badge ${statusClass(
                          action.status,
                        )}`}
                      >
                        {action.status}
                      </span>
                    </td>

                    <td>{action.attempt_count}</td>
                  </tr>
                ))}

                {!state.loading &&
                  state.recoveryActions.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="empty-cell"
                      >
                        No recovery records were returned.
                      </td>
                    </tr>
                  )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* WORKFLOW EXPLANATION */}

      <WorkflowOverview />

      {/* SYSTEM HEALTH */}

      <section className="dashboard-section">
        <div className="dashboard-section-heading">
          <div>
            <h2>System status</h2>

            <p>
              Live health checks from your FastAPI backend.
            </p>
          </div>
        </div>

        <div className="service-health-grid">
          <ServiceHealthCard
            title="Backend application"
            status={state.applicationStatus}
            description={
              state.health
                ? `${state.health.app_name} · ${state.health.environment}`
                : "Checking the application health endpoint."
            }
          />

          <ServiceHealthCard
            title="Database connection"
            status={state.databaseStatus}
            description={
              state.readiness
                ? `Database: ${state.readiness.database}`
                : "Checking database readiness."
            }
          />
        </div>
      </section>

      <p className="dashboard-last-updated">
        Dashboard data is fetched from the backend when
        this page loads or when you select Refresh.
      </p>
    </main>
  );
}