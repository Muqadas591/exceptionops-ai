import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { Link } from "react-router-dom";

import { api } from "../api";

import type {
  PaginatedResponse,
  WorkflowRun,
} from "../types";


function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}


export default function WorkflowHistoryPage() {
  const [workflows, setWorkflows] =
    useState<WorkflowRun[]>([]);

  const [status, setStatus] = useState("");
  const [documentId, setDocumentId] = useState("");

  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadWorkflows = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result: PaginatedResponse<WorkflowRun> =
        await api.getWorkflows(
          status || undefined,
          documentId ? Number(documentId) : undefined,
          limit,
          offset,
        );

      setWorkflows(result.items);
      setTotal(result.total ?? 0);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load workflows.",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId, limit, offset, status]);

  useEffect(() => {
    void loadWorkflows();
  }, [loadWorkflows]);

  function applyFilters() {
    setOffset(0);

    if (offset === 0) {
      void loadWorkflows();
    }
  }

  return (
    <main className="workflow-history-page">
      <header className="workflow-history-header">
        <div>
          <span className="workflow-eyebrow">
            OPERATIONS / PROCESSING
          </span>

          <h1>Workflow History</h1>

          <p>
            Inspect invoice workflow executions and their
            recorded lifecycle events.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadWorkflows()}
          disabled={loading}
        >
          Refresh
        </button>
      </header>

      <section className="workflow-filter-panel">
        <label>
          Workflow status
          <select
            value={status}
            onChange={(event) =>
              setStatus(event.target.value)
            }
          >
            <option value="">All statuses</option>
            <option value="received">Received</option>
            <option value="extracted">Extracted</option>
            <option value="evaluated">Evaluated</option>
            <option value="needs_review">Needs review</option>
            <option value="resolved">Resolved</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>

        <label>
          Document ID
          <input
            type="number"
            min="1"
            value={documentId}
            onChange={(event) =>
              setDocumentId(event.target.value)
            }
            placeholder="Optional document ID"
          />
        </label>

        <button
          type="button"
          onClick={applyFilters}
        >
          Apply filters
        </button>
      </section>

      {error && (
        <div className="workflow-error" role="alert">
          {error}
        </div>
      )}

      <section className="workflow-history-panel">
        <div className="workflow-history-panel-heading">
          <h2>Workflow executions</h2>
          <strong>{total} total</strong>
        </div>

        {loading ? (
          <p>Loading workflows...</p>
        ) : workflows.length === 0 ? (
          <p>No workflows found.</p>
        ) : (
          <div className="workflow-table-wrapper">
            <table className="workflow-table">
              <thead>
                <tr>
                  <th>Workflow</th>
                  <th>Document</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Events</th>
                  <th>Last updated</th>
                  <th>Details</th>
                </tr>
              </thead>

              <tbody>
                {workflows.map((workflow) => (
                  <tr key={workflow.id}>
                    <td>#{workflow.id}</td>
                    <td>#{workflow.document_id}</td>
                    <td>
                      <span
                        className={`workflow-status workflow-status-${workflow.status}`}
                      >
                        {workflow.status.replaceAll("_", " ")}
                      </span>
                    </td>
                    <td>{workflow.attempt_count}</td>
                    <td>{workflow.events.length}</td>
                    <td>{formatDate(workflow.updated_at)}</td>
                    <td>
                      <Link
                        to={`/workflows/${workflow.id}`}
                      >
                        View timeline
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer className="workflow-pagination">
        <button
          type="button"
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
          Showing {workflows.length} of {total}
        </span>

        <button
          type="button"
          disabled={
            offset + workflows.length >= total || loading
          }
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