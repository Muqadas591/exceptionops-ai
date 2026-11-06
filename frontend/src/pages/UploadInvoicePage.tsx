import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { uploadDocument } from "../api/documentsApi";
import type { DocumentRecord } from "../types/document";

const ALLOWED_EXTENSIONS = [".pdf", ".txt", ".csv"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

function validateFile(file: File): string | null {
  const extension = file.name
    .slice(file.name.lastIndexOf("."))
    .toLowerCase();

  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return "Unsupported file type. Please select a PDF, TXT, or CSV file.";
  }

  if (file.size === 0) {
    return "The selected file is empty.";
  }

  if (file.size > MAX_FILE_SIZE) {
    return "The selected file exceeds the default 10 MB upload limit.";
  }

  return null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} bytes`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function UploadInvoicePage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const [uploadedDocument, setUploadedDocument] =
    useState<DocumentRecord | null>(null);

  function handleFileSelection(file?: File) {
    setError("");
    setUploadedDocument(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const validationError = validateFile(file);

    if (validationError) {
      setSelectedFile(null);
      setError(validationError);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile || isUploading) {
      return;
    }

    setError("");
    setIsUploading(true);

    try {
      const result = await uploadDocument(selectedFile);

      setUploadedDocument(result);
      setSelectedFile(null);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "An unexpected upload error occurred.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <main className="invoice-page">
      <div className="invoice-page-heading">
        <div>
          <span className="eyebrow">DOCUMENT MANAGEMENT</span>
          <h1>Upload invoice</h1>
          <p>
            Add an invoice document to the ExceptionOps
            processing workflow.
          </p>
        </div>

        <Link to="/invoices" className="secondary-button">
          View invoices
        </Link>
      </div>

      <section className="upload-card">
        <div className="upload-icon" aria-hidden="true">
          ↑
        </div>

        <h2>Select an invoice document</h2>

        <p>
          Supported formats: PDF, TXT, and CSV.
          The default maximum file size is 10 MB.
        </p>

        <label
          className="file-picker"
          htmlFor="invoice-file"
        >
          Choose a file
        </label>

        <input
          ref={inputRef}
          id="invoice-file"
          type="file"
          accept=".pdf,.txt,.csv,application/pdf,text/plain,text/csv"
          disabled={isUploading}
          onChange={(event) =>
            handleFileSelection(
              event.target.files?.[0],
            )
          }
        />

        {selectedFile && (
          <div className="selected-file">
            <div>
              <strong>{selectedFile.name}</strong>
              <span>{formatFileSize(selectedFile.size)}</span>
            </div>

            <button
              type="button"
              className="text-button"
              disabled={isUploading}
              onClick={() => {
                setSelectedFile(null);

                if (inputRef.current) {
                  inputRef.current.value = "";
                }
              }}
            >
              Remove
            </button>
          </div>
        )}

        {error && (
          <div className="feedback-message error-message" role="alert">
            <strong>Upload failed</strong>
            <span>{error}</span>
          </div>
        )}

        {isUploading && (
          <div className="upload-progress" role="status">
            <div className="spinner" />
            <span>
              Uploading document and saving its metadata...
            </span>
          </div>
        )}

        {uploadedDocument && (
          <div className="feedback-message success-message" role="status">
            <strong>Document uploaded successfully</strong>
            <span>
              {uploadedDocument.original_filename} has been
              stored and registered as document #
              {uploadedDocument.id}.
            </span>

            <div className="success-actions">
              <button
                type="button"
                className="primary-button"
                onClick={() =>
                  navigate(
                    `/invoices/${uploadedDocument.id}`,
                  )
                }
              >
                View document
              </button>

              <Link to="/invoices">
                View all invoices
              </Link>
            </div>
          </div>
        )}

        <button
          type="button"
          className="primary-button upload-submit"
          disabled={!selectedFile || isUploading}
          onClick={handleUpload}
        >
          {isUploading ? "Uploading..." : "Upload invoice"}
        </button>
      </section>

      <section className="upload-information">
        <h3>What happens after upload?</h3>

        <ol>
          <li>The backend validates the file type and content.</li>
          <li>The document is saved in the configured local storage directory.</li>
          <li>Document metadata is registered in the database.</li>
          <li>The document becomes available for the next processing stage.</li>
        </ol>

        <p>
          Uploading a document does not automatically mean
          that extraction or business evaluation has completed.
        </p>
      </section>
    </main>
  );
}