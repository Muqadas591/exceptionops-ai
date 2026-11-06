import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import StatusBadge from "./StatusBadge";

import type {
  ActionExecution,
  ActionType,
  BusinessEvaluation,
  ExtractionResult,
  HumanReview,
  WorkflowRun,
} from "../types";

function displayField(value: unknown): string {
  if (
    value &&
    typeof value === "object" &&
    "value" in value
  ) {
    return displayField((value as { value: unknown }).value);
  }

  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export default function ReviewPage() {
  const { reviewId } = useParams<{ reviewId: string }>();
  const { user } = useAuth();

  const [review, setReview] = useState<HumanReview | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowRun | null>(null);
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);
  const [evaluation, setEvaluation] = useState<BusinessEvaluation | null>(null);
  const [action, setAction] = useState<ActionExecution | null>(null);

  const [reviewer, setReviewer] = useState("");
  const [comment, setComment] = useState("");
  const [correction, setCorrection] = useState("");
  const [decisionNote, setDecisionNote] = useState("");

  const [actionType, setActionType] =
    useState<ActionType>("accounting_simulation");
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("Invoice clarification");
  const [message, setMessage] = useState(
    "Please confirm the invoice details for our review.",
  );

  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const numericReviewId = Number(reviewId);

  const loadReview = useCallback(async () => {
    if (!Number.isInteger(numericReviewId) || numericReviewId <= 0) {
      setError("Invalid review ID.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const currentReview = await api.getReview(numericReviewId);

      setReview(currentReview);
      setReviewer(currentReview.assigned_to || "");

      const currentWorkflow = await api.getWorkflow(
        currentReview.workflow_run_id,
      );

      setWorkflow(currentWorkflow);

      const [extractionResult, evaluationResult] =
        await Promise.allSettled([
          api.getExtraction(currentWorkflow.document_id),
          api.getEvaluation(currentWorkflow.document_id),
        ]);

      setExtraction(
        extractionResult.status === "fulfilled"
          ? extractionResult.value
          : null,
      );

      setEvaluation(
        evaluationResult.status === "fulfilled"
          ? evaluationResult.value
          : null,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load this review.",
      );
    } finally {
      setLoading(false);
    }
  }, [numericReviewId]);

  useEffect(() => {
    void loadReview();
  }, [loadReview]);

  async function runOperation(
    operation: () => Promise<HumanReview>,
    successMessage: string,
  ) {
    setBusy(true);
    setError("");
    setNotice("");

    try {
      const updatedReview = await operation();
      setReview(updatedReview);
      setNotice(successMessage);
      await loadReview();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "The operation failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleAssign(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!review) return;

    await runOperation(
      () => api.assignReviewer(review.id, reviewer),
      "Reviewer assignment saved.",
    );
  }

  async function handleComment(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!review) return;

    await runOperation(
      () => api.addComment(review.id, comment),
      "Comment added.",
    );

    setComment("");
  }

  async function handleCorrection(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!review) return;

    await runOperation(
      () => api.requestCorrection(review.id, correction),
      "Correction request recorded.",
    );

    setCorrection("");
  }

  async function handleDecision(
    decision: "approve" | "reject",
  ) {
    if (!review) return;

    if (decisionNote.trim().length < 3) {
      setError("Enter a decision note of at least 3 characters.");
      return;
    }

    await runOperation(
      () =>
        decision === "approve"
          ? api.approveReview(review.id, decisionNote)
          : api.rejectReview(review.id, decisionNote),
      decision === "approve"
        ? "Review approved."
        : "Review rejected.",
    );

    setDecisionNote("");
  }

  async function handleAction(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!review) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const payload =
        actionType === "email_draft"
          ? {
              action_type: actionType,
              recipient,
              subject,
              message,
            }
          : { action_type: actionType };

      const result = await api.executeAction(
        review.id,
        payload,
      );

      setAction(result);
      setNotice(
        result.status === "succeeded"
          ? "Connector action completed."
          : "Action failed. Inspect the recorded outcome.",
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Action execution failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleRetryAction() {
    if (!action) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const result = await api.retryAction(action.id);
      setAction(result);
      setNotice(
        result.status === "succeeded"
          ? "Retry completed successfully."
          : "Retry failed. Inspect the saved error.",
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Retry failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleReadAction() {
    if (!action) return;

    setBusy(true);
    setError("");

    try {
      const result = await api.getAction(action.id);
      setAction(result);
      setNotice("Action outcome refreshed.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load action.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading && !review) {
    return (
      <main className="page">
        <p className="muted">Loading review…</p>
      </main>
    );
  }

  if (!review) {
    return (
      <main className="page">
        <Link className="back-link" to="/">← Back to queue</Link>
        {error && <div className="notice notice-error">{error}</div>}
        <button
          className="button button-secondary"
          onClick={() => void loadReview()}
        >
          Try again
        </button>
      </main>
    );
  }

  const finalDecision =
    review.status === "approved" || review.status === "rejected";

  const canDecide =
    Boolean(review.assigned_to) && !finalDecision;
  const canExecuteAction =
    user?.role === "admin" || user?.role === "action_operator";

  return (
    <main className="page">
      <Link className="back-link" to="/">
        ← Back to exception queue
      </Link>

      <div className="page-heading review-heading">
        <div>
          <p className="eyebrow">REVIEW WORKSPACE</p>
          <h2>Review #{review.id}</h2>
          <p className="muted">
            Workflow #{review.workflow_run_id}
            {workflow ? ` · Document #${workflow.document_id}` : ""}
          </p>
        </div>

        <StatusBadge status={review.status} />
      </div>

      {notice && <div className="notice notice-success">{notice}</div>}
      {error && <div className="notice notice-error">{error}</div>}

      <div className="review-layout">
        <div className="review-main">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Extracted invoice fields</h3>
                <p className="muted">
                  Values returned by the extraction service.
                </p>
              </div>
            </div>

            {extraction ? (
              <div className="field-grid">
                {Object.entries(extraction.fields || {}).map(
                  ([key, value]) => (
                    <div className="field-card" key={key}>
                      <span>{key.replaceAll("_", " ")}</span>
                      <strong>{displayField(value)}</strong>
                      {value &&
                        typeof value === "object" &&
                        "confidence" in value && (
                          <small>
                            Confidence:{" "}
                            {String(
                              (value as { confidence?: unknown })
                                .confidence ?? "—",
                            )}
                          </small>
                        )}
                    </div>
                  ),
                )}
              </div>
            ) : (
              <p className="muted">
                Extraction details are unavailable. Check the extraction
                endpoint and response schema.
              </p>
            )}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Business evaluation</h3>
                <p className="muted">
                  Rules findings from Phase 4.
                </p>
              </div>
            </div>

            {evaluation ? (
              <>
                <div className="evaluation-summary">
                  <div>
                    <span className="muted">Decision</span>
                    <StatusBadge status={evaluation.decision} />
                  </div>

                  <div>
                    <span className="muted">Risk score</span>
                    <strong>{evaluation.risk_score}/100</strong>
                  </div>

                  <div>
                    <span className="muted">Rules version</span>
                    <strong>{evaluation.rules_version}</strong>
                  </div>
                </div>

                <p>{evaluation.summary}</p>

                <h4>Findings</h4>

                {evaluation.findings.length ? (
                  <ul className="finding-list">
                    {evaluation.findings.map((finding, index) => (
                      <li key={`${finding.rule_code || "finding"}-${index}`}>
                        <strong>{finding.rule_code || "Rule finding"}</strong>
                        <p>
                          {finding.message || JSON.stringify(finding)}
                        </p>
                        {finding.severity && (
                          <span className="muted">
                            Severity: {finding.severity}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No findings were returned.</p>
                )}
              </>
            ) : (
              <p className="muted">
                No evaluation result is available for this document.
              </p>
            )}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Reviewer assignment</h3>
                <p className="muted">
                  Assign an owner before making a final decision.
                </p>
              </div>
            </div>

            <form className="inline-form" onSubmit={handleAssign}>
              <label className="grow">
                Reviewer identifier
                <input
                  value={reviewer}
                  onChange={(event) => setReviewer(event.target.value)}
                  placeholder="reviewer@example.test"
                  minLength={3}
                  maxLength={255}
                  required
                  disabled={finalDecision}
                />
              </label>

              <button
                className="button button-primary"
                type="submit"
                disabled={busy || finalDecision}
              >
                Assign reviewer
              </button>
            </form>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Comments and corrections</h3>
                <p className="muted">
                  Record questions and correction instructions.
                </p>
              </div>
            </div>

            <form className="stack-form" onSubmit={handleComment}>
              <label>
                Add a comment
                <textarea
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Add a note for the review history..."
                  required
                  maxLength={4000}
                  rows={3}
                  disabled={finalDecision}
                />
              </label>

              <button
                className="button button-secondary"
                type="submit"
                disabled={busy || finalDecision}
              >
                Add comment
              </button>
            </form>

            <div className="form-divider" />

            <form className="stack-form" onSubmit={handleCorrection}>
              <label>
                Request a correction
                <textarea
                  value={correction}
                  onChange={(event) => setCorrection(event.target.value)}
                  placeholder="Explain which field or document detail needs checking..."
                  required
                  minLength={3}
                  maxLength={4000}
                  rows={3}
                  disabled={finalDecision}
                />
              </label>

              <button
                className="button button-secondary"
                type="submit"
                disabled={busy || finalDecision}
              >
                Request correction
              </button>
            </form>

            <div className="comment-list">
              {review.comments.map((item) => (
                <article className="comment-item" key={item.id}>
                  <div className="comment-meta">
                    <strong>{item.author}</strong>
                    <span>{item.comment_type.replaceAll("_", " ")}</span>
                    <time>{new Date(item.created_at).toLocaleString()}</time>
                  </div>
                  <p>{item.body}</p>
                </article>
              ))}

              {review.comments.length === 0 && (
                <p className="muted">No comments yet.</p>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Review decision</h3>
                <p className="muted">
                  A decision note is required and will be recorded.
                </p>
              </div>
            </div>

            {finalDecision ? (
              <div className="notice notice-info">
                Final decision: <strong>{review.status}</strong>
                {review.decision_note
                  ? ` — ${review.decision_note}`
                  : ""}
              </div>
            ) : (
              <>
                {!review.assigned_to && (
                  <div className="notice notice-info">
                    Assign a reviewer before approving or rejecting.
                  </div>
                )}

                <label>
                  Decision note
                  <textarea
                    value={decisionNote}
                    onChange={(event) => setDecisionNote(event.target.value)}
                    minLength={3}
                    maxLength={2000}
                    rows={3}
                    placeholder="Explain why this review is being approved or rejected."
                    disabled={!canDecide}
                  />
                </label>

                <div className="button-row">
                  <button
                    className="button button-primary"
                    onClick={() => void handleDecision("approve")}
                    disabled={busy || !canDecide}
                  >
                    Approve
                  </button>

                  <button
                    className="button button-danger"
                    onClick={() => void handleDecision("reject")}
                    disabled={busy || !canDecide}
                  >
                    Reject
                  </button>
                </div>
              </>
            )}
          </section>

          {review.status === "approved" && (
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h3>Authorized actions</h3>
                  <p className="muted">
                    Email creates a draft. Accounting and webhook actions
                    are simulations only.
                  </p>
                </div>
              </div>

              <form className="stack-form" onSubmit={handleAction}>
                <label>
                  Connector action
                  <select
                    value={actionType}
                    onChange={(event) =>
                      setActionType(event.target.value as ActionType)
                    }
                  >
                    <option value="accounting_simulation">
                      Accounting simulation
                    </option>
                    <option value="webhook_simulation">
                      Webhook simulation
                    </option>
                    <option value="email_draft">
                      Create email draft
                    </option>
                  </select>
                </label>

                {actionType === "email_draft" && (
                  <>
                    <label>
                      Recipient
                      <input
                        type="email"
                        value={recipient}
                        onChange={(event) => setRecipient(event.target.value)}
                        placeholder="supplier@example.test"
                        required
                      />
                    </label>

                    <label>
                      Subject
                      <input
                        value={subject}
                        onChange={(event) => setSubject(event.target.value)}
                        required
                        maxLength={250}
                      />
                    </label>

                    <label>
                      Draft message
                      <textarea
                        value={message}
                        onChange={(event) => setMessage(event.target.value)}
                        required
                        maxLength={5000}
                        rows={4}
                      />
                    </label>
                  </>
                )}

                <button
                  className="button button-primary"
                  type="submit"
                  disabled={busy || !canExecuteAction}
                >
                  Execute selected action
                </button>
              </form>

              {action && (
                <div className="action-result">
                  <div className="panel-heading">
                    <h4>Action #{action.id}</h4>
                    <StatusBadge status={action.status} />
                  </div>

                  <p className="muted">
                    Type: {action.action_type.replaceAll("_", " ")}
                    {" · "}
                    Attempts: {action.attempt_count}
                  </p>

                  {action.last_error && (
                    <div className="notice notice-error">
                      {action.last_error}
                    </div>
                  )}

                  <pre className="json-output">
                    {JSON.stringify(action.result_payload, null, 2)}
                  </pre>

                  <div className="button-row">
                    <button
                      className="button button-secondary"
                      onClick={() => void handleReadAction()}
                      disabled={busy}
                    >
                      Refresh outcome
                    </button>

                    {action.status === "failed" && (
                      <button
                        className="button button-secondary"
                        onClick={() => void handleRetryAction()}
                        disabled={busy}
                      >
                        Retry action
                      </button>
                    )}
                  </div>
                </div>
              )}
            </section>
          )}
        </div>

        <aside className="review-sidebar">
          <section className="panel">
            <h3>Workflow overview</h3>

            {workflow ? (
              <dl className="detail-list">
                <dt>Workflow ID</dt>
                <dd>#{workflow.id}</dd>

                <dt>Document ID</dt>
                <dd>#{workflow.document_id}</dd>

                <dt>Workflow status</dt>
                <dd><StatusBadge status={workflow.status} /></dd>

                <dt>Attempts</dt>
                <dd>{workflow.attempt_count}</dd>

                <dt>Created</dt>
                <dd>{new Date(workflow.created_at).toLocaleString()}</dd>
              </dl>
            ) : (
              <p className="muted">Workflow information unavailable.</p>
            )}

            {workflow?.last_error && (
              <div className="notice notice-error">
                {workflow.last_error}
              </div>
            )}
          </section>

          <section className="panel">
            <h3>Workflow history</h3>

            {workflow?.events.length ? (
              <div className="timeline">
                {workflow.events.map((event) => (
                  <article className="timeline-item" key={event.id}>
                    <span className="timeline-dot" />
                    <div>
                      <strong>
                        {event.event_type.replaceAll("_", " ")}
                      </strong>
                      <p>{event.message}</p>
                      {event.to_status && (
                        <StatusBadge status={event.to_status} />
                      )}
                      <time>
                        {new Date(event.created_at).toLocaleString()}
                      </time>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">
                No workflow events are available.
              </p>
            )}
          </section>
        </aside>
      </div>
    </main>
  );
}