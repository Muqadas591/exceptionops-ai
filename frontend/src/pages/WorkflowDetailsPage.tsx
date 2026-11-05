import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { Link, useParams } from "react-router-dom";

import { api } from "../api";

import type {
  AuditEvent,
  WorkflowRun,
} from "../types";


function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}


export default function WorkflowDetailsPage() {
  const { workflowId } = useParams();

  const id =
    workflowId && /^\d+$/.test(workflowId)
      ? Number(workflowId)
      : null;

  const [workflow, setWorkflow] =
    useState<WorkflowRun | null>(null);

  const [auditEvents, setAuditEvents] =
    useState<AuditEvent[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDetails = useCallback(async () => {
    if (id === null) {
      setError("Invalid workflow ID.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const [workflowResult, auditResult] =
        await Promise.all([
          api.getWorkflow(id),
          api.getAuditEvents({
            workflow_run_id: id,
            limit: 100,
            offset: 0,
          }),
        ]);

      setWorkflow(workflowResult);
      setAuditEvents(auditResult.items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load workflow details.",
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadDetails();
  }, [loadDetails]);

  if (loading) {
    return (
      <main className="workflow-history-page">
        <p>Loading workflow timeline...</p>
      </main>
    );
  }

  if (!workflow) {
    return (
      <main className="workflow-history-page">
        <div className="workflow-error">
          {error || "Workflow not found."}
        </div>

        <Link to="/workflows">
          Back to workflow history
        </Link>
      </main>
    );
  }

  return (
    <main className="workflow-history-page">
      <header className="workflow-history-header">
        <div>
          <span className="workflow-eyebrow">
            WORKFLOW / TIMELINE
          </span>

          <h1>Workflow #{workflow.id}</h1>

          <p>
            Trace document processing and related audit events.
          </p>
        </div>

        <div className="workflow-detail-actions">
          <button
            type="button"
            onClick={() => void loadDetails()}
          >
            Refresh
          </button>

          <Link to="/workflows">
            Back to history
          </Link>
        </div>
      </header>

      <section className="workflow-summary">
        <div>
          <span>Document</span>
          <strong>
            <Link to={`/invoices/${workflow.document_id}`}>
              #{workflow.document_id}
            </Link>
          </strong>
        </div>

        <div>
          <span>Status</span>
          <strong>
            {workflow.status.replaceAll("_", " ")}
          </strong>
        </div>

        <div>
          <span>Attempts</span>
          <strong>{workflow.attempt_count}</strong>
        </div>

        <div>
          <span>Workflow events</span>
          <strong>{workflow.events.length}</strong>
        </div>
      </section>

      {workflow.last_error && (
        <section className="workflow-error">
          <strong>Last error</strong>
          <p>{workflow.last_error}</p>
        </section>
      )}

      {workflow.resolution_note && (
        <section className="workflow-history-panel">
          <h2>Resolution note</h2>
          <p>{workflow.resolution_note}</p>
        </section>
      )}

      <section className="workflow-history-panel">
        <h2>Workflow events</h2>

        {workflow.events.length === 0 ? (
          <p>No workflow events recorded.</p>
        ) : (
          <div className="workflow-event-list">
            {workflow.events.map((event) => (
              <article
                key={event.id}
                className="workflow-event-item"
              >
                <div>
                  <strong>
                    {event.event_type.replaceAll("_", " ")}
                  </strong>

                  <time>
                    {formatDate(event.created_at)}
                  </time>
                </div>

                <p>{event.message}</p>

                <small>
                  {event.from_status ?? "Start"}
                  {" → "}
                  {event.to_status ?? "No status change"}
                </small>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="workflow-history-panel">
        <h2>Related central audit events</h2>

        {auditEvents.length === 0 ? (
          <p>
            No central audit events are available for this workflow.
          </p>
        ) : (
          <div className="workflow-event-list">
            {auditEvents.map((event) => (
              <article
                key={event.id}
                className="workflow-event-item"
              >
                <div>
                  <strong>{event.event_type}</strong>
                  <time>{formatDate(event.created_at)}</time>
                </div>

                <p>{event.description}</p>

                <small>
                  Actor: {event.actor_id ?? event.actor_type}
                </small>

                <div className="audit-event-links">
                  {event.document_id !== null && (
                    <Link
                      to={`/invoices/${event.document_id}`}
                    >
                      Document #{event.document_id}
                    </Link>
                  )}

                  {event.review_id !== null && (
                    <Link to={`/reviews/${event.review_id}`}>
                      Review #{event.review_id}
                    </Link>
                  )}

                  {event.action_id !== null && (
                    <Link to="/actions">
                      Action #{event.action_id}
                    </Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}