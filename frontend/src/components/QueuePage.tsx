import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import StatusBadge from "./StatusBadge";
import type { AuthTokens, HumanReview } from "../types";

interface QueuePageProps {
  tokens: AuthTokens;
}

export default function QueuePage({ tokens }: QueuePageProps) {
  const navigate = useNavigate();

  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [status, setStatus] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadQueue = useCallback(async () => {
    if (!tokens.reviewerToken.trim()) {
      setError("Enter your reviewer token in the header.");
      setReviews([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await api.getQueue(
        tokens,
        status || undefined,
        assignedTo.trim() || undefined,
      );

      setReviews(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load the queue.",
      );
    } finally {
      setLoading(false);
    }
  }, [tokens, status, assignedTo]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  async function handleCreateReview(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");
    setNotice("");

    const parsedId = Number(workflowId);

    if (!Number.isInteger(parsedId) || parsedId <= 0) {
      setError("Enter a valid positive workflow ID.");
      return;
    }

    try {
      const review = await api.createReview(parsedId, tokens);
      setNotice(`Review #${review.id} is ready.`);
      navigate(`/reviews/${review.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create the review.",
      );
    }
  }

  const pendingCount = reviews.filter(
    (review) =>
      review.status === "pending" ||
      review.status === "correction_requested",
  ).length;

  const approvedCount = reviews.filter(
    (review) => review.status === "approved",
  ).length;

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS</p>
          <h2>Exception queue</h2>
          <p className="muted">
            Review invoice exceptions, assign ownership and track decisions.
          </p>
        </div>

        <button className="button button-secondary" onClick={() => void loadQueue()}>
          Refresh queue
        </button>
      </div>

      <section className="stats-grid">
        <article className="stat-card">
          <span className="muted">Reviews shown</span>
          <strong>{reviews.length}</strong>
          <span className="stat-caption">Current filters</span>
        </article>

        <article className="stat-card">
          <span className="muted">Awaiting attention</span>
          <strong>{pendingCount}</strong>
          <span className="stat-caption">Pending or correction requested</span>
        </article>

        <article className="stat-card">
          <span className="muted">Approved</span>
          <strong>{approvedCount}</strong>
          <span className="stat-caption">In the current result set</span>
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Find a review</h3>
            <p className="muted">
              Filter existing reviews or open one by its ID.
            </p>
          </div>
        </div>

        <div className="filters">
          <label>
            Review status
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="correction_requested">
                Correction requested
              </option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>

          <label>
            Assigned reviewer
            <input
              value={assignedTo}
              onChange={(event) => setAssignedTo(event.target.value)}
              placeholder="Filter by reviewer"
            />
          </label>

          <button
            className="button button-primary filter-button"
            onClick={() => void loadQueue()}
          >
            Apply filters
          </button>
        </div>

        <form className="create-review-form" onSubmit={handleCreateReview}>
          <label>
            Start from workflow ID
            <input
              type="number"
              min="1"
              value={workflowId}
              onChange={(event) => setWorkflowId(event.target.value)}
              placeholder="For example, 12"
              required
            />
          </label>

          <button className="button button-primary" type="submit">
            Open workflow review
          </button>
        </form>
      </section>

      {notice && <div className="notice notice-success">{notice}</div>}
      {error && <div className="notice notice-error">{error}</div>}

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h3>Review queue</h3>
            <p className="muted">
              Select a row to inspect the invoice and its review history.
            </p>
          </div>
          {loading && <span className="muted">Loading…</span>}
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
                <th />
              </tr>
            </thead>

            <tbody>
              {reviews.map((review) => (
                <tr key={review.id}>
                  <td>
                    <strong>#{review.id}</strong>
                  </td>
                  <td>#{review.workflow_run_id}</td>
                  <td>{review.assigned_to || "Unassigned"}</td>
                  <td>
                    <StatusBadge status={review.status} />
                  </td>
                  <td>
                    {new Date(review.updated_at).toLocaleString()}
                  </td>
                  <td>
                    <button
                      className="button button-small button-secondary"
                      onClick={() => navigate(`/reviews/${review.id}`)}
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}

              {!loading && reviews.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-cell">
                    No reviews found. Create a review from an evaluated
                    workflow or change the filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}