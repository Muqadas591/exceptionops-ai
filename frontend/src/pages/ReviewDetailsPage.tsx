import {
  useCallback,
  useEffect,
  useState,
} from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { getDocument } from "../api/documentsApi";
import { processingApi } from "../api/processingApi";
import { reviewsApi } from "../api/reviewApi";
import ReviewComments from "../components/reviews/ReviewComments";
import ReviewDecisionPanel from "../components/reviews/ReviewDecisionPanel";
import ReviewStatusBadge from "../components/reviews/ReviewStatusBadge";

import type {
  BusinessEvaluation,
  ExtractionResult,
  WorkflowRun,
} from "../types/processing";
import type {
  DocumentRecord,
} from "../types/document";
import type {
  HumanReview,
} from "../types/review";


function isNotFound(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "statusCode" in error &&
    error.statusCode === 404
  );
}

async function optionalRequest<T>(
  operation: () => Promise<T>,
): Promise<T | null> {
  try {
    return await operation();
  } catch (error) {
    if (isNotFound(error)) {
      return null;
    }

    throw error;
  }
}

export default function ReviewDetailsPage() {
  const { reviewId } = useParams();

  const numericReviewId =
    reviewId && /^\d+$/.test(reviewId)
      ? Number(reviewId)
      : null;

  const [review, setReview] =
    useState<HumanReview | null>(null);
  const [workflow, setWorkflow] =
    useState<WorkflowRun | null>(null);
  const [document, setDocument] =
    useState<DocumentRecord | null>(null);
  const [extraction, setExtraction] =
    useState<ExtractionResult | null>(null);
  const [evaluation, setEvaluation] =
    useState<BusinessEvaluation | null>(null);
  const [reviewer, setReviewer] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const completed =
    review?.status === "approved" ||
    review?.status === "rejected";

  const loadReview = useCallback(async () => {
    if (numericReviewId === null) {
      setReview(null);
      setError("Invalid review ID.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const reviewResult = await reviewsApi.getReview(
        numericReviewId,
      );
      setReview(reviewResult);

      const workflowResult =
        await processingApi.getWorkflow(
          reviewResult.workflow_run_id,
        );
      setWorkflow(workflowResult);

      const [
        documentResult,
        extractionResult,
        evaluationResult,
      ] = await Promise.all([
        getDocument(workflowResult.document_id),
        optionalRequest(() =>
          processingApi.getExtraction(
            workflowResult.document_id,
          ),
        ),
        optionalRequest(() =>
          processingApi.getEvaluation(
            workflowResult.document_id,
          ),
        ),
      ]);

      setDocument(documentResult);
      setExtraction(extractionResult);
      setEvaluation(evaluationResult);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load review details.",
      );
    } finally {
      setLoading(false);
    }
  }, [numericReviewId]);

  useEffect(() => {
    void loadReview();
  }, [loadReview]);

  function applyReviewUpdate(updated: HumanReview) {
    setReview(updated);
    setSuccess("Review updated successfully.");
    setError("");
  }

  async function handleAssign(
  event: FormEvent<HTMLFormElement>,
) {
    event.preventDefault();

    if (!review || !reviewer.trim()) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const updated = await reviewsApi.assignReviewer(
        review.id,
        reviewer.trim(),
      );
      applyReviewUpdate(updated);
      setReviewer("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to assign reviewer.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddComment(body: string) {
    if (!review) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const updated = await reviewsApi.addComment(
        review.id,
        body,
      );
      applyReviewUpdate(updated);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to add comment.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCorrection(
    instructions: string,
  ) {
    if (!review) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const updated =
        await reviewsApi.requestCorrection(
          review.id,
          instructions,
        );
      applyReviewUpdate(updated);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to request correction.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleApprove(note: string) {
    if (!review) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const updated = await reviewsApi.approve(
        review.id,
        note,
      );
      applyReviewUpdate(updated);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to approve review.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReject(note: string) {
    if (!review) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const updated = await reviewsApi.reject(
        review.id,
        note,
      );
      applyReviewUpdate(updated);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reject review.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="reviews-page">
        <div className="review-empty">
          Loading human-review workspace...
        </div>
      </main>
    );
  }

  if (!review) {
    return (
      <main className="reviews-page">
        <div className="review-error" role="alert">
          {error || "Review not found."}
        </div>
        <Link to="/exceptions">
          Back to exception queue
        </Link>
      </main>
    );
  }

  return (
    <main className="reviews-page">
      <div className="reviews-page-heading">
        <div>
          <span className="review-eyebrow">
            OPERATIONS / HUMAN REVIEW
          </span>
          <h1>Review #{review.id}</h1>
          <p>
            Inspect invoice information, review findings,
            and record a decision.
          </p>
        </div>

        <div className="review-heading-actions">
          <ReviewStatusBadge status={review.status} />
          <button
            type="button"
            className="review-secondary-button"
            onClick={() => void loadReview()}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
          <Link
            to="/exceptions"
            className="review-secondary-button"
          >
            Back to queue
          </Link>
        </div>
      </div>

      {error && (
        <div className="review-error" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="review-success" role="status">
          {success}
        </div>
      )}

      <section className="review-summary-grid">
        <div>
          <span>Review ID</span>
          <strong>#{review.id}</strong>
        </div>
        <div>
          <span>Workflow ID</span>
          <strong>#{review.workflow_run_id}</strong>
        </div>
        <div>
          <span>Assigned reviewer</span>
          <strong>{review.assigned_to || "Unassigned"}</strong>
        </div>
        <div>
          <span>Workflow status</span>
          <strong>
            {workflow?.status.replaceAll("_", " ") || "Unavailable"}
          </strong>
        </div>
      </section>

      <div className="review-workspace-grid">
        <div className="review-main-column">
          <section className="review-card">
            <div className="review-section-heading">
              <div>
                <h2>Invoice information</h2>
                <p>Document details associated with this review.</p>
              </div>
            </div>

            {document ? (
              <>
                <div className="review-document-details">
                  <div>
                    <span>Document ID</span>
                    <strong>#{document.id}</strong>
                  </div>
                  <div>
                    <span>Filename</span>
                    <strong>{document.original_filename}</strong>
                  </div>
                  <div>
                    <span>File type</span>
                    <strong>{document.extension.toUpperCase()}</strong>
                  </div>
                  <div>
                    <span>Document status</span>
                    <strong>{document.status}</strong>
                  </div>
                </div>
                <Link
                  to={`/invoices/${document.id}/process`}
                  className="review-open-link"
                >
                  Open processing workspace
                </Link>
              </>
            ) : (
              <div className="review-warning">
                Document metadata could not be loaded.
              </div>
            )}
          </section>

          <section className="review-card">
            <div className="review-section-heading">
              <div>
                <h2>Business evaluation findings</h2>
                <p>Findings returned by the backend evaluation.</p>
              </div>
            </div>

            {!evaluation ? (
              <div className="review-empty">
                No evaluation result is available for this document.
              </div>
            ) : (
              <>
                <div className="review-evaluation-summary">
                  <div>
                    <span>Decision</span>
                    <strong>
                      {evaluation.decision.replaceAll("_", " ")}
                    </strong>
                  </div>
                  <div>
                    <span>Risk score</span>
                    <strong>{evaluation.risk_score}/100</strong>
                  </div>
                  <div>
                    <span>Rules version</span>
                    <strong>{evaluation.rules_version}</strong>
                  </div>
                </div>

                <p className="review-evaluation-text">
                  {evaluation.summary}
                </p>

                {evaluation.findings.length === 0 ? (
                  <div className="review-success">
                    No business findings were returned.
                  </div>
                ) : (
                  <div className="review-findings">
                    {evaluation.findings.map(
                      (finding, index) => (
                        <article
                          key={`${finding.rule_code}-${index}`}
                          className="review-finding"
                        >
                          <div>
                            <strong>{finding.rule_code}</strong>
                            <span
                              className={`severity-badge severity-${finding.severity}`}
                            >
                              {finding.severity}
                            </span>
                          </div>
                          <p>{finding.message}</p>
                          {finding.field && (
                            <small>
                              Field: {finding.field}
                            </small>
                          )}
                        </article>
                      ),
                    )}
                  </div>
                )}
              </>
            )}
          </section>

          <section className="review-card">
            <div className="review-section-heading">
              <div>
                <h2>Extracted invoice fields</h2>
                <p>
                  Review the extracted values before making a decision.
                </p>
              </div>
            </div>

            {!extraction ? (
              <div className="review-empty">
                No extraction result is available.
              </div>
            ) : (
              <div className="review-extracted-fields">
                {Object.entries(extraction.fields).map(
                  ([name, field]) => (
                    <div
                      className="review-extracted-field"
                      key={name}
                    >
                      <span>{name.replaceAll("_", " ")}</span>
                      <strong>
                        {field.value ?? "Not extracted"}
                      </strong>
                      <small>
                        Confidence:{" "}
                        {typeof field.confidence === "number"
                          ? `${(field.confidence * 100).toFixed(1)}%`
                          : "Not provided"}
                      </small>
                      {field.evidence && <p>{field.evidence}</p>}
                    </div>
                  ),
                )}
              </div>
            )}
          </section>

          <ReviewComments
            comments={review.comments}
            completed={Boolean(completed)}
            submitting={submitting}
            onAddComment={handleAddComment}
            onRequestCorrection={handleCorrection}
          />
        </div>

        <aside className="review-side-column">
          <section className="review-card">
            <h2>Assignment</h2>
            <p className="review-help-text">
              Assign this review to a reviewer using the reviewer
              identifier expected by your backend.
            </p>
            <div className="review-current-assignee">
              <span>Current assignment</span>
              <strong>{review.assigned_to || "Unassigned"}</strong>
            </div>

            {!completed ? (
              <form
                className="review-assignment-form"
                onSubmit={handleAssign}
              >
                <label htmlFor="reviewer-name">
                  Reviewer identifier
                </label>
                <input
                  id="reviewer-name"
                  value={reviewer}
                  onChange={(event) =>
                    setReviewer(event.target.value)
                  }
                  placeholder="e.g. reviewer@example.com"
                  minLength={3}
                  maxLength={255}
                  required
                />
                <button
                  type="submit"
                  className="review-primary-button"
                  disabled={
                    submitting || reviewer.trim().length < 3
                  }
                >
                  {submitting
                    ? "Saving..."
                    : review.assigned_to
                      ? "Reassign review"
                      : "Assign reviewer"}
                </button>
              </form>
            ) : (
              <div className="review-info">
                Completed reviews cannot be reassigned.
              </div>
            )}
          </section>

          <ReviewDecisionPanel
            assigned={Boolean(review.assigned_to)}
            completed={Boolean(completed)}
            submitting={submitting}
            onApprove={handleApprove}
            onReject={handleReject}
          />

          {review.decision_note && (
            <section className="review-card">
              <h2>Recorded decision</h2>
              <p>{review.decision_note}</p>
              <span className="review-help-text">
                Decided by: {review.decided_by || "Not supplied"}
              </span>
            </section>
          )}

          <section className="review-card">
            <h2>Review metadata</h2>
            <div className="review-metadata-list">
              <div>
                <span>Created</span>
                <strong>
                  {new Date(review.created_at).toLocaleString()}
                </strong>
              </div>
              <div>
                <span>Last updated</span>
                <strong>
                  {new Date(review.updated_at).toLocaleString()}
                </strong>
              </div>
              <div>
                <span>Discussion events</span>
                <strong>{review.comments.length}</strong>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
