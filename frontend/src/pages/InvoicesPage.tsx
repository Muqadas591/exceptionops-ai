import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getDocuments } from "../api/documentsApi";
import type { DocumentRecord } from "../types/document";

const PAGE_SIZE = 20;

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function InvoicesPage() {
  const [documents, setDocuments] =
    useState<DocumentRecord[]>([]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [offset, setOffset] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await getDocuments({
        limit: PAGE_SIZE,
        offset,
      });

      setDocuments(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load documents.",
      );
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const filteredDocuments = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return documents.filter((document) => {
      const matchesSearch =
        !normalizedSearch ||
        document.original_filename
          .toLowerCase()
          .includes(normalizedSearch) ||
        String(document.id).includes(normalizedSearch);

      const matchesStatus =
        statusFilter === "all" ||
        document.status.toLowerCase() ===
          statusFilter.toLowerCase();

      return matchesSearch && matchesStatus;
    });
  }, [documents, search, statusFilter]);

  const hasNextPage = documents.length === PAGE_SIZE;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <main className="invoice-page">
      <div className="invoice-page-heading">
        <div>
          <span className="eyebrow">DOCUMENT MANAGEMENT</span>
          <h1>Invoices</h1>
          <p>
            Browse and manage invoice documents received
            by the platform.
          </p>
        </div>

        <Link
          to="/invoices/upload"
          className="primary-button"
        >
          + Upload invoice
        </Link>
      </div>

      <section className="invoice-toolbar">
        <input
          type="search"
          placeholder="Search filename or document ID..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          aria-label="Search invoices"
        />

        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
          aria-label="Filter by document status"
        >
          <option value="all">All statuses</option>
          <option value="received">Received</option>
          <option value="extracted">Extracted</option>
          <option value="evaluated">Evaluated</option>
          <option value="failed">Failed</option>
        </select>

        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadDocuments()}
          disabled={loading}
        >
          Refresh
        </button>
      </section>

      {error && (
        <div className="feedback-message error-message" role="alert">
          {error}
        </div>
      )}

      <section className="invoice-table-card">
        {loading ? (
          <div className="table-state">
            Loading documents...
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="table-state">
            <h3>No documents found</h3>
            <p>
              Upload an invoice or change your search
              and filter criteria.
            </p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="invoice-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Document ID</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredDocuments.map((document) => (
                  <tr key={document.id}>
                    <td>
                      <strong>
                        {document.original_filename}
                      </strong>
                    </td>

                    <td>#{document.id}</td>

                    <td>
                      {document.extension.toUpperCase()}
                    </td>

                    <td>
                      {formatSize(document.file_size_bytes)}
                    </td>

                    <td>
                      <span
                        className={`document-status status-${document.status.toLowerCase()}`}
                      >
                        {document.status.replaceAll("_", " ")}
                      </span>
                    </td>

                    <td>{formatDate(document.created_at)}</td>

                    <td>
                      <Link
                        to={`/invoices/${document.id}`}
                        className="table-link"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="pagination-bar">
        <span>Page {currentPage}</span>

        <div>
          <button
            type="button"
            className="secondary-button"
            disabled={offset === 0 || loading}
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
            className="secondary-button"
            disabled={!hasNextPage || loading}
            onClick={() =>
              setOffset((current) => current + PAGE_SIZE)
            }
          >
            Next
          </button>
        </div>
      </div>

      <p className="table-footnote">
        Showing {filteredDocuments.length} matching documents
        from the currently loaded page. The backend document
        list endpoint does not currently provide a total-count
        header.
      </p>
    </main>
  );
}