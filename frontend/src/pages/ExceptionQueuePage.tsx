import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { reviewsApi } from "../api/reviewApi";
import ReviewStatusBadge from "../components/reviews/ReviewStatusBadge";

import type {
  HumanReview,
  ReviewStatusFilter,
} from "../types/review";

const PAGE_SIZE = 20;

export default function ExceptionQueuePage() {
  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const [status, setStatus] =
    useState<ReviewStatusFilter>("");

  const [assignedTo, setAssignedTo] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await reviewsApi.getQueue({
        status,
        assignedTo,
        limit: PAGE_SIZE,
        offset,
      });

      setReviews(result.items);
      setTotal(result.total);
      setHasMore(result.hasMore);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load the exception queue.",
      );
    } finally {
      setLoading(false);
    }
  }, [status, assignedTo, offset]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  function updateStatus(value: ReviewStatusFilter) {
    setOffset(0);
    setStatus(value);
  }

  function updateAssignee(value: string) {
    setOffset(0);
    setAssignedTo(value);
  }

  const pageNumber = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(
    1,
    Math.ceil(total / PAGE_SIZE),
  );

  return (
    <main className="reviews-page">
      <div className="reviews-page-heading">
        <div>
          <span className="review-eyebrow">
            OPERATIONS / HUMAN REVIEW
          </span>

          <h1>Exception Queue</h1>

          <p>
            Review invoices that require human attention,
            track assignments, and record decisions.
          </p>
        </div>

        <button
          type="button"
          className="review-secondary-button"
          onClick={() => void loadQueue()}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh queue"}
        </button>
      </div>

      <section className="review-metrics">
        <div>
          <span>Matching reviews</span>
          <strong>{total}</strong>
        </div>

        <div>
          <span>On this page</span>
          <strong>{reviews.length}</strong>
        </div>

        <div>
          <span>Page</span>
          <strong>
            {pageNumber} / {totalPages}
          </strong>
        </div>
      </section>

      <section className="review-card">
        <div className="review-section-heading">
          <div>
            <h2>Review records</h2>
            <p>
              Filter the queue by review status or assigned reviewer.
            </p>
          </div>
        </div>

        <div className="review-filters">
          <label>
            Review status

            <select
              value={status}
              onChange={(event) =>
                updateStatus(
                  event.target.value as ReviewStatusFilter,
                )
              }
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
              onChange={(event) =>
                updateAssignee(event.target.value)
              }
              placeholder="Exact reviewer identifier"
            />
          </label>

          <button
            type="button"
            className="review-secondary-button"
            onClick={() => {
              setOffset(0);
              setStatus("");
              setAssignedTo("");
            }}
          >
            Clear filters
          </button>
        </div>

        {error && (
          <div className="review-error" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="review-empty">
            Loading exception queue...
          </div>
        ) : reviews.length === 0 ? (
          <div className="review-empty">
            <h3>No review records found</h3>
            <p>
              There are no reviews matching the selected filters.
              Reviews are created from eligible invoice workflows.
            </p>
          </div>
        ) : (
          <div className="review-table-wrapper">
            <table className="review-table">
              <thead>
                <tr>
                  <th>Review ID</th>
                  <th>Workflow ID</th>
                  <th>Assigned reviewer</th>
                  <th>Status</th>
                  <th>Comments</th>
                  <th>Updated</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {reviews.map((review) => (
                  <tr key={review.id}>
                    <td>#{review.id}</td>

                    <td>#{review.workflow_run_id}</td>

                    <td>
                      {review.assigned_to || "Unassigned"}
                    </td>

                    <td>
                      <ReviewStatusBadge
                        status={review.status}
                      />
                    </td>

                    <td>{review.comments.length}</td>

                    <td>
                      {new Date(
                        review.updated_at,
                      ).toLocaleDateString()}
                    </td>

                    <td>
                      <Link
                        to={`/reviews/${review.id}`}
                        className="review-open-link"
                      >
                        Open review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="review-pagination">
          <span>
            Showing {reviews.length ? offset + 1 : 0}
            {"–"}
            {offset + reviews.length} of {total}
          </span>

          <div>
            <button
              type="button"
              className="review-secondary-button"
              disabled={loading || offset === 0}
              onClick={() =>
                setOffset((current) =>
                  Math.max(0, current - PAGE_SIZE),
                )
              }
            >
              Previous
            </button>

            <button
              type="button"
              className="review-secondary-button"
              disabled={loading || !hasMore}
              onClick={() =>
                setOffset((current) =>
                  current + PAGE_SIZE,
                )
              }
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}