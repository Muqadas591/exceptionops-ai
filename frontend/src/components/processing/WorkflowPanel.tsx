import type { WorkflowRun } from "../../types/processing";

interface WorkflowPanelProps {
  workflow: WorkflowRun | null;
  loading: boolean;
  starting: boolean;
  advancing: boolean;
  retrying: boolean;
  disabled: boolean;
  error: string;
  onStart: () => void;
  onAdvance: () => void;
  onRetry: () => void;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

export default function WorkflowPanel({
  workflow,
  loading,
  starting,
  advancing,
  retrying,
  disabled,
  error,
  onStart,
  onAdvance,
  onRetry,
}: WorkflowPanelProps) {
  const canAdvance =
    workflow !== null &&
    workflow.status !== "evaluated" &&
    workflow.status !== "needs_review" &&
    workflow.status !== "resolved" &&
    workflow.status !== "failed" &&
    workflow.status !== "cancelled";

  return (
    <section className="processing-card">
      <div className="processing-card-heading">
        <div>
          <span className="processing-step">STEP 3</span>
          <h2>Workflow progression</h2>
          <p>
            Create and progress the backend workflow for
            this invoice.
          </p>
        </div>
      </div>

      {loading && (
        <div className="processing-empty">
          Loading workflow...
        </div>
      )}

      {error && (
        <div className="processing-error" role="alert">
          {error}
        </div>
      )}

      {!loading && !workflow && (
        <div className="workflow-start">
          <h3>No workflow has been created</h3>

          <p>
            Once extraction and business evaluation are complete,
            create a workflow to record the processing lifecycle.
          </p>

          <button
            type="button"
            className="processing-primary-button"
            onClick={onStart}
            disabled={disabled || starting}
          >
            {starting ? "Starting..." : "Start workflow"}
          </button>
        </div>
      )}

      {workflow && (
        <>
          <div className="workflow-overview">
            <div>
              <span>Workflow ID</span>
              <strong>#{workflow.id}</strong>
            </div>

            <div>
              <span>Current status</span>
              <strong
                className={`workflow-status workflow-${workflow.status}`}
              >
                {statusLabel(workflow.status)}
              </strong>
            </div>

            <div>
              <span>Attempts</span>
              <strong>{workflow.attempt_count}</strong>
            </div>
          </div>

          {workflow.last_error && (
            <div className="processing-error">
              <strong>Last workflow error</strong>
              <p>{workflow.last_error}</p>
            </div>
          )}

          {workflow.resolution_note && (
            <div className="processing-info">
              <strong>Resolution note</strong>
              <p>{workflow.resolution_note}</p>
            </div>
          )}

          <div className="workflow-actions">
            <button
              type="button"
              className="processing-primary-button"
              onClick={onAdvance}
              disabled={
                disabled ||
                advancing ||
                !canAdvance
              }
            >
              {advancing
                ? "Advancing..."
                : "Advance workflow"}
            </button>

            {workflow.status === "failed" && (
              <button
                type="button"
                className="processing-secondary-button"
                onClick={onRetry}
                disabled={disabled || retrying}
              >
                {retrying ? "Retrying..." : "Retry workflow"}
              </button>
            )}
          </div>

          {workflow.status === "needs_review" && (
            <div className="processing-warning">
              This workflow requires human review. Continue
              in the Exception Queue / Review Workspace.
            </div>
          )}

          {workflow.status === "evaluated" && (
            <div className="processing-success">
              Workflow evaluation completed. The next stage
              can proceed according to the business process.
            </div>
          )}

          <div className="workflow-timeline">
            <h3>Workflow event history</h3>

            {workflow.events.length === 0 ? (
              <p className="processing-muted">
                No workflow events have been recorded.
              </p>
            ) : (
              <ol>
                {workflow.events.map((event) => (
                  <li key={event.id}>
                    <div className="timeline-marker" />

                    <div className="timeline-content">
                      <strong>
                        {event.event_type.replaceAll("_", " ")}
                      </strong>

                      <p>{event.message}</p>

                      <span>
                        {formatDate(event.created_at)}
                      </span>

                      {(event.from_status || event.to_status) && (
                        <small>
                          {event.from_status || "Start"}
                          {" → "}
                          {event.to_status || "—"}
                        </small>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </>
      )}
    </section>
  );
}