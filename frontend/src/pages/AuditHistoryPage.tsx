import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { api } from "../api";

import type {
  AuditEvent,
  AuditEventFilters,
  PaginatedResponse,
} from "../types";


function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function eventLabel(value: string): string {
  return value
    .replaceAll(".", " ")
    .replaceAll("_", " ");
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Unable to load audit events.";
}


export default function AuditHistoryPage() {
  const { user } = useAuth();

  const [events, setEvents] =
    useState<AuditEvent[]>([]);

  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(25);

  const [eventType, setEventType] = useState("");
  const [entityType, setEntityType] = useState("");
  const [actorId, setActorId] = useState("");
  const [search, setSearch] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError("");

    const filters: AuditEventFilters = {
      limit,
      offset,
    };

    if (eventType.trim()) {
      filters.event_type = eventType.trim();
    }

    if (entityType) {
      filters.entity_type = entityType;
    }

    if (actorId.trim()) {
      filters.actor_id = actorId.trim();
    }

    if (search.trim()) {
      filters.search = search.trim();
    }

    if (fromDate) {
      filters.from_datetime = new Date(fromDate).toISOString();
    }

    if (toDate) {
      filters.to_datetime = new Date(toDate).toISOString();
    }

    try {
      const result: PaginatedResponse<AuditEvent> =
        await api.getAuditEvents(filters);

      setEvents(result.items);
      setTotal(result.total ?? 0);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [
    actorId,
    entityType,
    eventType,
    fromDate,
    limit,
    offset,
    search,
    toDate,
  ]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  function applyFilters() {
  setOffset(0);

  if (offset === 0) {
    void loadEvents();
  }
}

  return (
    <main className="audit-page">
      <header className="audit-page-header">
        <div>
          <span className="audit-eyebrow">
            OPERATIONS / GOVERNANCE
          </span>

          <h1>Audit History</h1>

          <p>
            Inspect recorded document, workflow, review,
            and action events.
          </p>
        </div>

        <button
          type="button"
          className="audit-button"
          onClick={() => void loadEvents()}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </header>

      <section className="audit-filter-panel">
        <label>
          Event type
          <input
            value={eventType}
            onChange={(event) =>
              setEventType(event.target.value)
            }
            placeholder="e.g. review.approved"
          />
        </label>

        <label>
          Entity
          <select
            value={entityType}
            onChange={(event) =>
              setEntityType(event.target.value)
            }
          >
            <option value="">All entities</option>
            <option value="document">Document</option>
            <option value="extraction">Extraction</option>
            <option value="evaluation">Evaluation</option>
            <option value="workflow">Workflow</option>
            <option value="human_review">Human review</option>
            <option value="action_execution">Action</option>
          </select>
        </label>

        <label>
          Actor
          <input
            value={actorId}
            onChange={(event) =>
              setActorId(event.target.value)
            }
            placeholder="Email or actor ID"
          />
        </label>

        <label>
          Description search
          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search event descriptions"
          />
        </label>

        <label>
          From
          <input
            type="datetime-local"
            value={fromDate}
            onChange={(event) =>
              setFromDate(event.target.value)
            }
          />
        </label>

        <label>
          To
          <input
            type="datetime-local"
            value={toDate}
            onChange={(event) =>
              setToDate(event.target.value)
            }
          />
        </label>

        <button
          type="button"
          className="audit-button audit-button-primary"
          onClick={applyFilters}
        >
          Apply filters
        </button>
      </section>

      {error && (
        <div className="audit-error" role="alert">
          {error}
        </div>
      )}

      <section className="audit-summary">
        <div>
          <span>Total matching events</span>
          <strong>{total}</strong>
        </div>

        <div>
          <span>Current page</span>
          <strong>
            {events.length === 0
              ? 0
              : Math.floor(offset / limit) + 1}
          </strong>
        </div>
      </section>

      <section className="audit-timeline-panel">
        <h2>Event timeline</h2>

        {loading ? (
          <p>Loading audit events...</p>
        ) : events.length === 0 ? (
          <p className="audit-empty">
            No events match the selected filters.
          </p>
        ) : (
          <div className="audit-timeline">
            {events.map((event) => (
              <article
                key={event.id}
                className="audit-event"
              >
                <div className="audit-event-marker" />

                <div className="audit-event-content">
                  <div className="audit-event-heading">
                    <strong>
                      {eventLabel(event.event_type)}
                    </strong>

                    <time>
                      {formatDate(event.created_at)}
                    </time>
                  </div>

                  <p>{event.description}</p>

                  <div className="audit-event-meta">
                    <span>
                      Entity: {event.entity_type}
                      {event.entity_id
                        ? ` #${event.entity_id}`
                        : ""}
                    </span>

                    <span>
                      Actor: {event.actor_id ?? event.actor_type}
                    </span>
                  </div>

                  <div className="audit-event-links">
                    {user?.role === "admin" && (
                      <>
                        {event.document_id !== null && (
                          <Link
                            to={`/invoices/${event.document_id}`}
                          >
                            Document #{event.document_id}
                          </Link>
                        )}

                        {event.workflow_run_id !== null && (
                          <Link
                            to={`/workflows/${event.workflow_run_id}`}
                          >
                            Workflow #{event.workflow_run_id}
                          </Link>
                        )}

                        {event.review_id !== null && (
                          <Link
                            to={`/reviews/${event.review_id}`}
                          >
                            Review #{event.review_id}
                          </Link>
                        )}
                      </>
                    )}

                    {event.action_id !== null && (
                      <Link
                        to={
                          event.review_id !== null
                            ? `/actions?reviewId=${event.review_id}`
                            : "/actions"
                        }
                      >
                        Action #{event.action_id}
                      </Link>
                    )}
                  </div>

                  {event.event_metadata &&
                    Object.keys(event.event_metadata).length > 0 && (
                      <details className="audit-event-details">
                        <summary>Event metadata</summary>
                        <pre>
                          {JSON.stringify(
                            event.event_metadata,
                            null,
                            2,
                          )}
                        </pre>
                      </details>
                    )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="audit-pagination">
        <button
          type="button"
          className="audit-button"
          disabled={offset === 0 || loading}
          onClick={() =>
            setOffset((value) =>
              Math.max(0, value - limit),
            )
          }
        >
          Previous
        </button>

        <span>
          Showing {events.length} of {total}
        </span>

        <button
          type="button"
          className="audit-button"
          disabled={offset + events.length >= total || loading}
          onClick={() =>
            setOffset((value) => value + limit)
          }
        >
          Next
        </button>
      </footer>
    </main>
  );
}