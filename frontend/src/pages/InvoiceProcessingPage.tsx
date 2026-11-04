import { useCallback, useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import { getDocument } from "../api/documentsApi";
import {
  processingApi,
  ProcessingApiError,
} from "../api/processingApi";

import type { DocumentRecord } from "../types/document";

import type {
  BusinessEvaluation,
  ExtractionResult,
  WorkflowRun,
} from "../types/processing";

import ExtractionPanel from "../components/processing/ExtractionPanel";
import EvaluationPanel from "../components/processing/EvaluationPanel";
import WorkflowPanel from "../components/processing/WorkflowPanel";
import { reviewsApi } from "../api/reviewApi";

function isNotFound(error: unknown): boolean {
  return (
    error instanceof ProcessingApiError &&
    error.statusCode === 404
  );
}

async function loadOptional<T>(
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

function evaluationIsOutdated(
  extraction: ExtractionResult | null,
  evaluation: BusinessEvaluation | null,
): boolean {
  if (!extraction || !evaluation) {
    return false;
  }

  return (
    new Date(extraction.updated_at).getTime() >
    new Date(evaluation.updated_at).getTime()
  );
}

export default function InvoiceProcessingPage() {
  const { documentId } = useParams();

  const numericDocumentId =
    documentId && /^\d+$/.test(documentId)
      ? Number(documentId)
      : null;

  const [document, setDocument] =
    useState<DocumentRecord | null>(null);

  const [extraction, setExtraction] =
    useState<ExtractionResult | null>(null);

  const [evaluation, setEvaluation] =
    useState<BusinessEvaluation | null>(null);

  const [workflow, setWorkflow] =
    useState<WorkflowRun | null>(null);

  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [extractionLoading, setExtractionLoading] =
    useState(false);

  const [evaluationLoading, setEvaluationLoading] =
    useState(false);

  const [workflowLoading, setWorkflowLoading] =
    useState(false);

  const [runningExtraction, setRunningExtraction] =
    useState(false);

  const [runningEvaluation, setRunningEvaluation] =
    useState(false);

  const [startingWorkflow, setStartingWorkflow] =
    useState(false);

  const [advancingWorkflow, setAdvancingWorkflow] =
    useState(false);

  const [retryingWorkflow, setRetryingWorkflow] =
    useState(false);

  const [extractionError, setExtractionError] = useState("");
  const [evaluationError, setEvaluationError] = useState("");
  const [workflowError, setWorkflowError] = useState("");

  const [evaluationStale, setEvaluationStale] =
    useState(false);
  const navigate = useNavigate();

  const [creatingReview, setCreatingReview] =
    useState(false);

  const [reviewCreationError, setReviewCreationError] =
    useState("");

  const loadWorkspace = useCallback(async () => {
    if (numericDocumentId === null) {
      setPageError("Invalid document ID.");
      setPageLoading(false);
      return;
    }

    setPageLoading(true);
    setPageError("");

    try {
      const documentResult = await getDocument(
        numericDocumentId,
      );

      setDocument(documentResult);

      setExtractionLoading(true);
      setEvaluationLoading(true);
      setWorkflowLoading(true);

      const [
        extractionResult,
        evaluationResult,
        workflowResult,
      ] = await Promise.all([
        loadOptional(() =>
          processingApi.getExtraction(numericDocumentId),
        ),

        loadOptional(() =>
          processingApi.getEvaluation(numericDocumentId),
        ),

        loadOptional(() =>
          processingApi.getDocumentWorkflow(numericDocumentId),
        ),
      ]);

      setExtraction(extractionResult);
      setEvaluation(evaluationResult);
      setWorkflow(workflowResult);

      setEvaluationStale(
        evaluationIsOutdated(
          extractionResult,
          evaluationResult,
        ),
      );

      setExtractionError("");
      setEvaluationError("");
      setWorkflowError("");
    } catch (error) {
      setPageError(
        error instanceof Error
          ? error.message
          : "Unable to load the processing workspace.",
      );
    } finally {
      setPageLoading(false);
      setExtractionLoading(false);
      setEvaluationLoading(false);
      setWorkflowLoading(false);
    }
  }, [numericDocumentId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  // ---------------------------------------
  // RUN EXTRACTION
  // ---------------------------------------

  async function handleRunExtraction() {
    if (numericDocumentId === null) return;

    setRunningExtraction(true);
    setExtractionError("");
    setEvaluationError("");

    try {
      const result = await processingApi.runExtraction(
        numericDocumentId,
      );

      setExtraction(result);

      // A new extraction must be evaluated again.
      setEvaluationStale(Boolean(evaluation));
      setEvaluation(null);
    } catch (error) {
      setExtractionError(
        error instanceof Error
          ? error.message
          : "Extraction failed.",
      );
    } finally {
      setRunningExtraction(false);
    }
  }

  // ---------------------------------------
  // RUN BUSINESS EVALUATION
  // ---------------------------------------

  async function handleRunEvaluation() {
    if (numericDocumentId === null || !extraction) {
      return;
    }

    setRunningEvaluation(true);
    setEvaluationError("");

    try {
      const result = await processingApi.runEvaluation(
        numericDocumentId,
      );

      setEvaluation(result);
      setEvaluationStale(false);
    } catch (error) {
      setEvaluationError(
        error instanceof Error
          ? error.message
          : "Business evaluation failed.",
      );
    } finally {
      setRunningEvaluation(false);
    }
  }

  // ---------------------------------------
  // CREATE WORKFLOW
  // ---------------------------------------

  async function handleStartWorkflow() {
    if (!extraction || !evaluation || evaluationStale) {
      setWorkflowError(
        "Complete extraction and current business evaluation first.",
      );
      return;
    }

    setStartingWorkflow(true);
    setWorkflowError("");

    try {
      const result = await processingApi.createWorkflow(
        numericDocumentId!,
      );

      setWorkflow(result);
    } catch (error) {
      setWorkflowError(
        error instanceof Error
          ? error.message
          : "Unable to start workflow.",
      );
    } finally {
      setStartingWorkflow(false);
    }
  }

  // ---------------------------------------
  // ADVANCE WORKFLOW
  // ---------------------------------------

  async function handleAdvanceWorkflow() {
    if (!workflow) return;

    if (!evaluation || evaluationStale) {
      setWorkflowError(
        "Run a current business evaluation before advancing.",
      );
      return;
    }

    setAdvancingWorkflow(true);
    setWorkflowError("");

    try {
      const result = await processingApi.advanceWorkflow(
        workflow.id,
      );

      setWorkflow(result);
    } catch (error) {
      setWorkflowError(
        error instanceof Error
          ? error.message
          : "Unable to advance workflow.",
      );
    } finally {
      setAdvancingWorkflow(false);
    }
  }

  // ---------------------------------------
  // RETRY FAILED WORKFLOW
  // ---------------------------------------

  async function handleRetryWorkflow() {
    if (!workflow) return;

    setRetryingWorkflow(true);
    setWorkflowError("");

    try {
      const result = await processingApi.retryWorkflow(
        workflow.id,
      );

      setWorkflow(result);
    } catch (error) {
      setWorkflowError(
        error instanceof Error
          ? error.message
          : "Unable to retry workflow.",
      );
    } finally {
      setRetryingWorkflow(false);
    }
  }

  async function handleCreateOrOpenReview() {
    if (!workflow) {
      setReviewCreationError(
        "Create a workflow before opening a human review.",
      );
      return;
    }

    if (
      workflow.status !== "evaluated" &&
      workflow.status !== "needs_review"
    ) {
      setReviewCreationError(
        "A review can only be created for an evaluated workflow or one requiring review.",
      );
      return;
    }

    setCreatingReview(true);
    setReviewCreationError("");

    try {
      const review = await reviewsApi.createReview(
        workflow.id,
      );

      navigate(`/reviews/${review.id}`);
    } catch (error) {
      setReviewCreationError(
        error instanceof Error
          ? error.message
          : "Unable to create or open the review.",
      );
    } finally {
      setCreatingReview(false);
    }
  }

  if (pageLoading) {
    return (
      <main className="processing-page">
        <div className="processing-page-state">
          Loading invoice processing workspace...
        </div>
      </main>
    );
  }

  if (pageError || !document) {
    return (
      <main className="processing-page">
        <div className="processing-error" role="alert">
          {pageError || "Document not found."}
        </div>

        <Link to="/invoices">
          Back to invoices
        </Link>
      </main>
    );
  }

  const workflowActionsDisabled =
    !extraction ||
    !evaluation ||
    evaluationStale;

  return (
    <main className="processing-page">
      <div className="processing-page-heading">
        <div>
          <span className="processing-eyebrow">
            INVOICE PROCESSING WORKSPACE
          </span>

          <h1>Process invoice</h1>

          <p>{document.original_filename}</p>
        </div>

        <div className="processing-page-actions">
          <Link
            to={`/invoices/${document.id}`}
            className="processing-secondary-button"
          >
            Document details
          </Link>

          <Link
            to="/invoices"
            className="processing-secondary-button"
          >
            All invoices
          </Link>

          <button
            type="button"
            className="processing-secondary-button"
            onClick={() => void loadWorkspace()}
          >
            Refresh
          </button>
        </div>
      </div>

      <section className="processing-document-banner">
        <div>
          <span>Document ID</span>
          <strong>#{document.id}</strong>
        </div>

        <div>
          <span>File type</span>
          <strong>{document.extension.toUpperCase()}</strong>
        </div>

        <div>
          <span>Document status</span>
          <strong>
            {document.status.replaceAll("_", " ")}
          </strong>
        </div>

        <div>
          <span>Uploaded</span>
          <strong>
            {new Date(document.created_at).toLocaleDateString()}
          </strong>
        </div>
      </section>

      <div className="processing-introduction">
        <h2>Processing pipeline</h2>

        <p>
          Execute extraction, inspect the extracted information,
          evaluate business rules, and progress the workflow.
          Each step uses the backend's persisted results.
        </p>
      </div>

      <ExtractionPanel
        extraction={extraction}
        loading={extractionLoading}
        running={runningExtraction}
        error={extractionError}
        onRunExtraction={handleRunExtraction}
      />

      <EvaluationPanel
        evaluation={evaluation}
        loading={evaluationLoading}
        running={runningEvaluation}
        disabled={!extraction}
        stale={evaluationStale}
        error={evaluationError}
        onRunEvaluation={handleRunEvaluation}
      />

      <WorkflowPanel
        workflow={workflow}
        loading={workflowLoading}
        starting={startingWorkflow}
        advancing={advancingWorkflow}
        retrying={retryingWorkflow}
        disabled={workflowActionsDisabled}
        error={workflowError}
        onStart={handleStartWorkflow}
        onAdvance={handleAdvanceWorkflow}
        onRetry={handleRetryWorkflow}
      />

      {workflow &&
        (workflow.status === "evaluated" ||
          workflow.status === "needs_review") && (
          <section className="processing-card">
            <div className="processing-card-heading">
              <div>
                <span className="processing-step">
                  HUMAN REVIEW
                </span>

                <h2>Exception review</h2>

                <p>
                  Create or open the human-review record
                  associated with this workflow.
                </p>
              </div>

              <button
                type="button"
                className="processing-primary-button"
                onClick={() =>
                  void handleCreateOrOpenReview()
                }
                disabled={creatingReview}
              >
                {creatingReview
                  ? "Opening review..."
                  : "Create / open human review"}
              </button>
            </div>

            {reviewCreationError && (
              <div
                className="processing-error"
                role="alert"
              >
                {reviewCreationError}
              </div>
            )}
          </section>
        )}

      <div className="processing-bottom-note">
        <strong>Control and safety note</strong>

        <p>
          Extraction and evaluation do not authorize payment.
          Workflow progression records the processing state.
          Human review and controlled actions remain separate
          stages of the platform.
        </p>
      </div>
    </main>
  );
}