import type {
  ActionExecution,
  ActionReconciliationRequest,
  ActionRequest,
  BusinessEvaluation,
  Document,
  ExtractionResult,
  HumanReview,
  LoginRequest,
  TokenResponse,
  User,
  WorkflowRun,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const AUTH_STORAGE_KEY = "exceptionops_access_token";

function getToken(): string | null {
  return sessionStorage.getItem(AUTH_STORAGE_KEY);
}

interface RequestOptions extends RequestInit {
  authenticated?: boolean;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    authenticated = true,
    ...fetchOptions
  } = options;

  const headers = new Headers(fetchOptions.headers);

  if (
    fetchOptions.body &&
    !(fetchOptions.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const token = getToken();

    if (!token) {
      throw new Error("Your session has expired. Please sign in again.");
    }

    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...fetchOptions,
      headers,
    },
  );

  const responseText = await response.text();

  let data: unknown = null;

  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch {
      data = responseText;
    }
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    if (
      data &&
      typeof data === "object" &&
      "detail" in data
    ) {
      const detail = (data as { detail: unknown }).detail;

      message =
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail);
    } else if (typeof data === "string" && data) {
      message = data;
    }

    if (
      authenticated &&
      response.status === 401
    ) {
      sessionStorage.removeItem(AUTH_STORAGE_KEY);

      window.dispatchEvent(
        new Event("exceptionops:session-expired"),
      );
    }

    throw new Error(message);
  }

  return data as T;
}

function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}

export const api = {
  // -----------------------------------
  // AUTHENTICATION
  // -----------------------------------

  login(payload: LoginRequest): Promise<TokenResponse> {
    return request<TokenResponse>(
      "/api/v1/auth/login",
      {
        method: "POST",
        authenticated: false,
        body: jsonBody(payload),
      },
    );
  },

  getCurrentUser(): Promise<User> {
    return request<User>("/api/v1/auth/me");
  },

  // -----------------------------------
  // HEALTH
  // -----------------------------------

  getHealth(): Promise<{
    status: string;
    app_name: string;
    environment: string;
  }> {
    return request(
      "/api/v1/health",
      { authenticated: false },
    );
  },

  getReadiness(): Promise<{
    status: string;
    database: string;
  }> {
    return request(
      "/api/v1/ready",
      { authenticated: false },
    );
  },

  // -----------------------------------
  // DOCUMENTS
  // -----------------------------------

  getDocuments(
    limit = 100,
    offset = 0,
  ): Promise<Document[]> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request(
      `/api/v1/documents?${query.toString()}`,
    );
  },

  getDocument(
    documentId: number,
  ): Promise<Document> {
    return request(
      `/api/v1/documents/${documentId}`,
    );
  },

  uploadDocument(
    file: File,
  ): Promise<Document> {
    const formData = new FormData();

    formData.append("file", file);

    return request(
      "/api/v1/documents",
      {
        method: "POST",
        body: formData,
      },
    );
  },

  async downloadDocument(
    documentId: number,
  ): Promise<Blob> {
    const token = getToken();

    if (!token) {
      throw new Error("Please sign in again.");
    }

    const response = await fetch(
      `${API_BASE_URL}/api/v1/documents/${documentId}/content`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!response.ok) {
      throw new Error(
        `Document download failed (${response.status}).`,
      );
    }

    return response.blob();
  },

  // -----------------------------------
  // EXTRACTION
  // -----------------------------------

  runExtraction(
    documentId: number,
  ): Promise<ExtractionResult> {
    return request(
      `/api/v1/documents/${documentId}/extract`,
      { method: "POST" },
    );
  },

  getExtraction(
    documentId: number,
  ): Promise<ExtractionResult> {
    return request(
      `/api/v1/documents/${documentId}/extraction`,
    );
  },

  // -----------------------------------
  // BUSINESS EVALUATION
  // -----------------------------------

  evaluateDocument(
    documentId: number,
  ): Promise<BusinessEvaluation> {
    return request(
      `/api/v1/documents/${documentId}/evaluate`,
      { method: "POST" },
    );
  },

  getEvaluation(
    documentId: number,
  ): Promise<BusinessEvaluation> {
    return request(
      `/api/v1/documents/${documentId}/evaluation`,
    );
  },

  // -----------------------------------
  // WORKFLOWS
  // -----------------------------------

  startWorkflow(
    documentId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/documents/${documentId}/workflow`,
      {
        method: "POST",
        headers: {
          "Idempotency-Key": crypto.randomUUID(),
        },
      },
    );
  },

  getDocumentWorkflow(
    documentId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/documents/${documentId}/workflow`,
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
      { method: "POST" },
    );
  },

  retryWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}/retry`,
      { method: "POST" },
    );
  },

  resolveWorkflow(
    workflowId: number,
    note: string,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}/resolve`,
      {
        method: "POST",
        body: jsonBody({ note }),
      },
    );
  },

  cancelWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request(
      `/api/v1/workflows/${workflowId}/cancel`,
      { method: "POST" },
    );
  },

  // -----------------------------------
  // HUMAN REVIEW
  // -----------------------------------

  getQueue(
    status?: string,
    assignedTo?: string,
    limit = 100,
    offset = 0,
  ): Promise<HumanReview[]> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    if (status) {
      query.set("status", status);
    }

    if (assignedTo) {
      query.set("assigned_to", assignedTo);
    }

    return request(
      `/api/v1/reviews/queue?${query.toString()}`,
    );
  },

  createReview(
    workflowId: number,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/workflows/${workflowId}/review`,
      { method: "POST" },
    );
  },

  getReview(
    reviewId: number,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}`,
    );
  },

  assignReviewer(
    reviewId: number,
    reviewer: string,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/assign`,
      {
        method: "POST",
        body: jsonBody({ reviewer }),
      },
    );
  },

  addComment(
    reviewId: number,
    body: string,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/comments`,
      {
        method: "POST",
        body: jsonBody({ body }),
      },
    );
  },

  requestCorrection(
    reviewId: number,
    instructions: string,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/request-correction`,
      {
        method: "POST",
        body: jsonBody({ instructions }),
      },
    );
  },

  approveReview(
    reviewId: number,
    note: string,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/approve`,
      {
        method: "POST",
        body: jsonBody({ note }),
      },
    );
  },

  rejectReview(
    reviewId: number,
    note: string,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/reject`,
      {
        method: "POST",
        body: jsonBody({ note }),
      },
    );
  },

  // -----------------------------------
  // ACTIONS
  // -----------------------------------

  executeAction(
    reviewId: number,
    payload: ActionRequest,
  ): Promise<ActionExecution> {
    return request(
      `/api/v1/reviews/${reviewId}/actions`,
      {
        method: "POST",
        headers: {
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: jsonBody(payload),
      },
    );
  },

  getAction(
    actionId: number,
  ): Promise<ActionExecution> {
    return request(
      `/api/v1/actions/${actionId}`,
    );
  },

  getRecoveryQueue(
    limit = 100,
    offset = 0,
  ): Promise<ActionExecution[]> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request(
      `/api/v1/actions/recovery/queue?${query.toString()}`,
    );
  },

  retryAction(
    actionId: number,
  ): Promise<ActionExecution> {
    return request(
      `/api/v1/actions/${actionId}/retry`,
      { method: "POST" },
    );
  },

  reconcileAction(
    actionId: number,
    payload: ActionReconciliationRequest,
  ): Promise<ActionExecution> {
    return request(
      `/api/v1/actions/${actionId}/reconcile`,
      {
        method: "POST",
        body: jsonBody(payload),
      },
    );
  },
};