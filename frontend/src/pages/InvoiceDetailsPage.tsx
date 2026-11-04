import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  downloadDocument,
  getDocument,
} from "../api/documentsApi";

import type { DocumentRecord } from "../types/document";

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function formatSize(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function InvoiceDetailsPage() {
  const { documentId } = useParams();

  const [document, setDocument] =
    useState<DocumentRecord | null>(null);

  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadDocument() {
      if (!documentId || !/^\d+$/.test(documentId)) {
        setError("Invalid document ID.");
        setLoading(false);
        return;
      }

      try {
        const result = await getDocument(Number(documentId));

        if (active) {
          setDocument(result);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load document details.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadDocument();

    return () => {
      active = false;
    };
  }, [documentId]);

  async function handleDownload() {
    if (!document) return;

    setDownloading(true);
    setError("");

    try {
      await downloadDocument(
        document.id,
        document.original_filename,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Download failed.",
      );
    } finally {
      setDownloading(false);
    }
  }

  if (loading) {
    return (
      <main className="invoice-page">
        <div className="table-state">
          Loading document details...
        </div>
      </main>
    );
  }

  if (error && !document) {
    return (
      <main className="invoice-page">
        <div className="feedback-message error-message" role="alert">
          {error}
        </div>

        <Link to="/invoices">Back to invoices</Link>
      </main>
    );
  }

  if (!document) {
    return null;
  }

  return (
    <main className="invoice-page">
      <div className="invoice-page-heading">
        <div>
          <span className="eyebrow">
            DOCUMENT #{document.id}
          </span>

          <h1>Invoice details</h1>

          <p>{document.original_filename}</p>
        </div>

        <div className="details-actions">
          <Link
            to="/invoices"
            className="secondary-button"
          >
            Back to invoices
          </Link>

          <Link
            to={`/invoices/${document.id}/process`}
            className="primary-button"
          >
            Open processing workspace
          </Link>

          <button
            type="button"
            className="primary-button"
            onClick={handleDownload}
            disabled={downloading}
          >
            {downloading ? "Downloading..." : "Download original"}
          </button>
        </div>
      </div>

      {error && (
        <div className="feedback-message error-message" role="alert">
          {error}
        </div>
      )}

      <section className="document-details-card">
        <h2>Document metadata</h2>

        <dl className="metadata-grid">
          <div>
            <dt>Document ID</dt>
            <dd>#{document.id}</dd>
          </div>

          <div>
            <dt>Original filename</dt>
            <dd>{document.original_filename}</dd>
          </div>

          <div>
            <dt>File extension</dt>
            <dd>{document.extension}</dd>
          </div>

          <div>
            <dt>Content type</dt>
            <dd>{document.content_type}</dd>
          </div>

          <div>
            <dt>File size</dt>
            <dd>{formatSize(document.file_size_bytes)}</dd>
          </div>

          <div>
            <dt>Processing status</dt>
            <dd>
              <span
                className={`document-status status-${document.status.toLowerCase()}`}
              >
                {document.status.replaceAll("_", " ")}
              </span>
            </dd>
          </div>

          <div>
            <dt>Uploaded</dt>
            <dd>{formatDate(document.created_at)}</dd>
          </div>

          <div>
            <dt>Last updated</dt>
            <dd>{formatDate(document.updated_at)}</dd>
          </div>

          <div className="metadata-full">
            <dt>SHA-256 checksum</dt>
            <dd className="checksum-value">
              {document.checksum_sha256}
            </dd>
          </div>
        </dl>
      </section>

      <section className="document-next-step">
        <h2>Processing status</h2>
        <p>
          This page displays the document's stored metadata.
          Extraction and business evaluation are separate
          processing operations and will be connected in
          Phase 4.
        </p>
      </section>
    </main>
  );
}