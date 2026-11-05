import {
  useCallback,
  useEffect,
  useState,
} from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import ActionStatusBadge from "../components/actions/ActionStatusBadge";
import { actionsApi } from "../api/actionApi";
import type {
  ActionExecution,
  ActionType,
  ReconciliationOutcome,
} from "../types/action";

const actionLabels: Record<ActionType, string> = {
  email_draft: "Create email draft",
  accounting_simulation: "Run accounting simulation",
  webhook_simulation: "Run webhook simulation",
};

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "An unexpected error occurred.";
}

export default function ActionCenterPage() {
  const [searchParams] = useSearchParams();
  const initialReviewId = searchParams.get("reviewId") ?? "";
  const [reviewId, setReviewId] = useState(initialReviewId);
  const [actionType, setActionType] =
    useState<ActionType>("accounting_simulation");

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");

  const [history, setHistory] = useState<ActionExecution[]>([]);
  const [recoveryItems, setRecoveryItems] =
    useState<ActionExecution[]>([]);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [reconcileActionId, setReconcileActionId] =
    useState<number | null>(null);
  const [reconcileOutcome, setReconcileOutcome] =
    useState<ReconciliationOutcome>("confirmed_not_executed");
  const [reconcileNote, setReconcileNote] = useState("");

  const loadRecoveryQueue = useCallback(async () => {
    const result = await actionsApi.getRecoveryQueue(50, 0);
    setRecoveryItems(result);
  }, []);

  const loadReviewHistory = useCallback(async () => {
    const id = Number(reviewId);

    if (!Number.isInteger(id) || id <= 0) {
      setHistory([]);
      return;
    }

    const result = await actionsApi.getReviewActions(id, 50, 0);
    setHistory(result);
  }, [reviewId]);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      await Promise.all([
        loadRecoveryQueue(),
        loadReviewHistory(),
      ]);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [loadRecoveryQueue, loadReviewHistory]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  async function handleCreateAction(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");
    setNotice("");

    const id = Number(reviewId);

    if (!Number.isInteger(id) || id <= 0) {
      setError("Enter a valid review ID.");
      return;
    }

    if (
      actionType === "email_draft" &&
      (!recipient.trim() ||
        !subject.trim() ||
        !message.trim())
    ) {
      setError(
        "Recipient, subject, and message are required for an email draft.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const payload =
        actionType === "email_draft"
          ? {
              action_type: actionType,
              recipient: recipient.trim(),
              subject: subject.trim(),
              message: message.trim(),
            }
          : {
              action_type: actionType,
            };

      // Generate a new key for a new logical action.
      // Do not generate a new key just to repeat a request whose
      // response may have been lost.
      const idempotencyKey = `exceptionops-${crypto.randomUUID()}`;

      const result = await actionsApi.createForReview(
        id,
        payload,
        idempotencyKey,
      );

      setNotice(
        `Action #${result.id} returned with status: ${result.status}.`,
      );

      await refreshAll();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRetry(actionId: number) {
    setError("");
    setNotice("");

    try {
      const result = await actionsApi.retry(actionId);

      setNotice(
        `Retry for action #${actionId} returned status: ${result.status}.`,
      );

      await refreshAll();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleReconcile(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (reconcileActionId === null) return;

    setError("");
    setNotice("");

    try {
      const result = await actionsApi.reconcile(
        reconcileActionId,
        {
          outcome: reconcileOutcome,
          note: reconcileNote.trim(),
        },
      );

      setNotice(
        `Action #${result.id} reconciled as ${result.status}.`,
      );

      setReconcileActionId(null);
      setReconcileNote("");

      await refreshAll();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <main className="actions-page">
      <header className="actions-page-header">
        <div>
          <p className="eyebrow">CONTROLLED OPERATIONS</p>
          <h1>Action Center</h1>
          <p>
            Execute approved-review actions, inspect execution history,
            and resolve recovery items.
          </p>
        </div>

        <button
          type="button"
          className="button button-secondary"
          onClick={() => void refreshAll()}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {error && (
        <div className="action-alert action-alert-error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="action-alert action-alert-success" role="status">
          {notice}
        </div>
      )}

      <section className="action-panel">
        <div className="action-panel-heading">
          <div>
            <h2>Execute an approved review action</h2>
            <p>
              The backend verifies that the review is approved before
              creating an execution.
            </p>
          </div>
        </div>

        <form onSubmit={handleCreateAction} className="action-form">
          <label>
            Approved review ID
            <input
              type="number"
              min="1"
              value={reviewId}
              onChange={(event) => setReviewId(event.target.value)}
              placeholder="Enter review ID"
              required
            />
          </label>

          <label>
            Action type
            <select
              value={actionType}
              onChange={(event) =>
                setActionType(event.target.value as ActionType)
              }
            >
              <option value="accounting_simulation">
                Accounting simulation
              </option>
              <option value="email_draft">Email draft</option>
              <option value="webhook_simulation">
                Webhook simulation
              </option>
            </select>
          </label>

          {actionType === "email_draft" && (
            <div className="email-draft-fields">
              <label>
                Recipient email
                <input
                  type="email"
                  value={recipient}
                  onChange={(event) => setRecipient(event.target.value)}
                  maxLength={320}
                  required
                />
              </label>

              <label>
                Subject
                <input
                  value={subject}
                  onChange={(event) => setSubject(event.target.value)}
                  maxLength={250}
                  required
                />
              </label>

              <label>
                Draft message
                <textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  maxLength={5000}
                  rows={5}
                  required
                />
              </label>
            </div>
          )}

          <p className="action-safety-note">
            {actionType === "email_draft"
              ? "This creates a draft only. It does not send an email."
              : actionType === "accounting_simulation"
                ? "This is a simulation. No accounting transaction is posted."
                : "This is a simulation. No external HTTP request is sent."}
          </p>

          <button
            type="submit"
            className="button button-primary"
            disabled={submitting}
          >
            {submitting ? "Executing..." : "Create and execute action"}
          </button>
        </form>
      </section>

      <section className="action-panel">
        <div className="action-panel-heading">
          <div>
            <h2>Recovery queue</h2>
            <p>
              Pending, in-progress, uncertain, and failed executions that
              need operator attention.
            </p>
          </div>
          <span className="action-count">{recoveryItems.length}</span>
        </div>

        {recoveryItems.length === 0 ? (
          <p className="empty-state">
            No recovery items were returned by the backend.
          </p>
        ) : (
          <div className="action-table-wrapper">
            <table className="action-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Review</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Updated</th>
                  <th>Operator controls</th>
                </tr>
              </thead>
              <tbody>
                {recoveryItems.map((item) => (
                  <tr key={item.id}>
                    <td>#{item.id}</td>
                    <td>#{item.review_id}</td>
                    <td>{actionLabels[item.action_type]}</td>
                    <td>
                      <ActionStatusBadge status={item.status} />
                    </td>
                    <td>{item.attempt_count}</td>
                    <td>{formatDate(item.updated_at)}</td>
                    <td>
                      <div className="action-row-controls">
                        {(item.status === "pending" ||
                          item.status === "failed") && (
                          <button
                            type="button"
                            className="button button-small"
                            onClick={() => void handleRetry(item.id)}
                          >
                            Retry
                          </button>
                        )}

                        {item.status === "uncertain" && (
                          <button
                            type="button"
                            className="button button-small"
                            onClick={() => {
                              setReconcileActionId(item.id);
                              setReconcileOutcome(
                                "confirmed_not_executed",
                              );
                              setReconcileNote("");
                            }}
                          >
                            Reconcile
                          </button>
                        )}

                        {item.status === "in_progress" && (
                          <span>
                            Execution is in progress. Do not reconcile yet.
                          </span>
                        )}
                      </div>

                      {item.last_error && (
                        <p className="action-error-detail">
                          {item.last_error}
                        </p>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {reconcileActionId !== null && (
        <section className="action-panel reconciliation-panel">
          <h2>Reconcile action #{reconcileActionId}</h2>

          <p>
            Only select an outcome after reviewing the execution evidence.
            Reconciliation does not run the connector.
          </p>

          <form onSubmit={handleReconcile} className="action-form">
            <label>
              Confirmed outcome
              <select
                value={reconcileOutcome}
                onChange={(event) =>
                  setReconcileOutcome(
                    event.target.value as ReconciliationOutcome,
                  )
                }
              >
                <option value="confirmed_not_executed">
                  Confirmed not executed
                </option>
                <option value="confirmed_succeeded">
                  Confirmed succeeded
                </option>
              </select>
            </label>

            <label>
              Operator explanation
              <textarea
                value={reconcileNote}
                onChange={(event) => setReconcileNote(event.target.value)}
                minLength={5}
                maxLength={1000}
                rows={3}
                required
              />
            </label>

            <div className="action-row-controls">
              <button type="submit" className="button button-primary">
                Save reconciliation
              </button>

              <button
                type="button"
                className="button button-secondary"
                onClick={() => setReconcileActionId(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="action-panel">
        <div className="action-panel-heading">
          <div>
            <h2>Execution history</h2>
            <p>
              Enter a review ID above to inspect its recorded actions.
            </p>
          </div>
        </div>

        {history.length === 0 ? (
          <p className="empty-state">
            No action history is available for this review.
          </p>
        ) : (
          <div className="action-table-wrapper">
            <table className="action-table">
              <thead>
                <tr>
                  <th>Action ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Executed by</th>
                  <th>Created</th>
                  <th>Last error</th>
                  <th>Controls</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td>#{item.id}</td>
                    <td>{actionLabels[item.action_type]}</td>
                    <td>
                      <ActionStatusBadge status={item.status} />
                    </td>
                    <td>{item.attempt_count}</td>
                    <td>{item.executed_by}</td>
                    <td>{formatDate(item.created_at)}</td>
                    <td>{item.last_error ?? "—"}</td>
                    <td>
                      {item.status === "failed" && (
                        <button
                          type="button"
                          className="button button-small"
                          onClick={() => void handleRetry(item.id)}
                        >
                          Retry
                        </button>
                      )}

                      {item.status === "uncertain" && (
                        <span>Requires reconciliation</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}