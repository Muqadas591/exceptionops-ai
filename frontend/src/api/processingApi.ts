import type {
  BusinessEvaluation,
  ExtractionResult,
  WorkflowRun,
} from "../types/processing";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const AUTH_STORAGE_KEY = "exceptionops_access_token";

export class ProcessingApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ProcessingApiError";
    this.statusCode = statusCode;
  }
}

function getHeaders(): Headers {
  const token = sessionStorage.getItem(AUTH_STORAGE_KEY);

  if (!token) {
    throw new Error(
      "Your session is missing. Please sign in again.",
    );
  }

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);

  return headers;
}

async function parseError(
  response: Response,
): Promise<string> {
  const text = await response.text();

  if (!text) {
    return `Request failed with status ${response.status}.`;
  }

  try {
    const data: unknown = JSON.parse(text);

    if (
      data &&
      typeof data === "object" &&
      "detail" in data
    ) {
      const detail = (data as { detail: unknown }).detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (
              item &&
              typeof item === "object" &&
              "msg" in item
            ) {
              return String(
                (item as { msg: unknown }).msg,
              );
            }

            return JSON.stringify(item);
          })
          .join(" ");
      }

      return JSON.stringify(detail);
    }

    return JSON.stringify(data);
  } catch {
    return text;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = getHeaders();

  new Headers(options.headers).forEach((value, key) => {
    headers.set(key, value);
  });

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (response.status === 401) {
    window.dispatchEvent(
      new Event("session-expired"),
    );

    throw new ProcessingApiError(
      "Your session has expired. Please sign in again.",
      401,
    );
  }

  if (!response.ok) {
    throw new ProcessingApiError(
      await parseError(response),
      response.status,
    );
  }

  return (await response.json()) as T;
}

export const processingApi = {
  // -----------------------------
  // INVOICE EXTRACTION
  // -----------------------------

  runExtraction(
    documentId: number,
  ): Promise<ExtractionResult> {
    return request(
      `/api/v1/documents/${documentId}/extract`,
      {
        method: "POST",
      },
    );
  },

  getExtraction(
    documentId: number,
  ): Promise<ExtractionResult> {
    return request(
      `/api/v1/documents/${documentId}/extraction`,
    );
  },

  // -----------------------------
  // BUSINESS EVALUATION
  // -----------------------------

  runEvaluation(
    documentId: number,
  ): Promise<BusinessEvaluation> {
    return request(
      `/api/v1/documents/${documentId}/evaluate`,
      {
        method: "POST",
      },
    );
  },

  getEvaluation(
    documentId: number,
  ): Promise<BusinessEvaluation> {
    return request(
      `/api/v1/documents/${documentId}/evaluation`,
    );
  },

  // -----------------------------
  // WORKFLOW
  // -----------------------------

  getDocumentWorkflow(
    documentId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/documents/${documentId}/workflow`,
    );
  },

  createWorkflow(
    documentId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/documents/${documentId}/workflow`,
      {
        method: "POST",
        headers: {
          // Stable per document: prevents accidental duplicate
          // workflow creation when a reviewer retries the request.
          "Idempotency-Key":
            `exceptionops-document-${documentId}`,
        },
      },
    );
  },

  getWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}`,
    );
  },

  advanceWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}/advance`,
      {
        method: "POST",
      },
    );
  },

  retryWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}/retry`,
      {
        method: "POST",
      },
    );
  },
};