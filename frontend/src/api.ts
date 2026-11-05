import type {
  ActionExecution,
  ActionType,
  BusinessEvaluation,
  Document,
  ExtractionResult,
  HealthResponse,
  HumanReview,
  LoginRequest,
  PaginatedResponse,
  ReadinessResponse,
  TokenResponse,
  User,
  WorkflowRun,
  AuditEvent,
  AuditEventFilters,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const AUTH_STORAGE_KEY =
  "exceptionops_access_token";

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
    const token = sessionStorage.getItem(
      AUTH_STORAGE_KEY,
    );

    if (!token) {
      throw new Error(
        "Your session has expired. Please sign in again.",
      );
    }

    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
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
      const detail = (
        data as { detail: unknown }
      ).detail;

      if (typeof detail === "string") {
        message = detail;
      } else {
        message = JSON.stringify(detail);
      }
    } else if (
      typeof data === "string" &&
      data.length > 0
    ) {
      message = data;
    }

    if (
      authenticated &&
      response.status === 401
    ) {
      sessionStorage.removeItem(
        AUTH_STORAGE_KEY,
      );

      window.dispatchEvent(
        new Event("exceptionops:session-expired"),
      );
    }

    throw new Error(message);
  }

  return data as T;
}

async function requestWithHeaders<T>(
  path: string,
  options: RequestOptions = {},
): Promise<{
  data: T;
  headers: Headers;
}> {
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
    const token = sessionStorage.getItem(
      AUTH_STORAGE_KEY,
    );

    if (!token) {
      throw new Error(
        "Your session has expired. Please sign in again.",
      );
    }

    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...fetchOptions,
      headers,
    },
  );

  const text = await response.text();

  let data: unknown = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    if (
      data &&
      typeof data === "object" &&
      "detail" in data
    ) {
      const detail = (
        data as { detail: unknown }
      ).detail;

      message =
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail);
    }

    if (
      authenticated &&
      response.status === 401
    ) {
      sessionStorage.removeItem(
        AUTH_STORAGE_KEY,
      );

      window.dispatchEvent(
        new Event("exceptionops:session-expired"),
      );
    }

    throw new Error(message);
  }

  return {
    data: data as T,
    headers: response.headers,
  };
}

function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}

function readNumberHeader(
  headers: Headers,
  name: string,
): number | null {
  const value = headers.get(name);

  if (!value) {
    return null;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed)
    ? parsed
    : null;
}

export const api = {
  // =====================================
  // AUTHENTICATION
  // =====================================

  login(
    payload: LoginRequest,
  ): Promise<TokenResponse> {
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
    return request<User>(
      "/api/v1/auth/me",
    );
  },

  // =====================================
  // SYSTEM HEALTH
  // =====================================

  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>(
      "/api/v1/health",
      {
        authenticated: false,
      },
    );
  },

  getReadiness(): Promise<ReadinessResponse> {
    return request<ReadinessResponse>(
      "/api/v1/ready",
      {
        authenticated: false,
      },
    );
  },

  // =====================================
  // DOCUMENTS
  // =====================================

  getDocuments(
    limit = 100,
    offset = 0,
  ): Promise<Document[]> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request<Document[]>(
      `/api/v1/documents?${query.toString()}`,
    );
  },

  getDocument(
    documentId: number,
  ): Promise<Document> {
    return request<Document>(
      `/api/v1/documents/${documentId}`,
    );
  },

  uploadDocument(
    file: File,
  ): Promise<Document> {
    const formData = new FormData();

    formData.append("file", file);

    return request<Document>(
      "/api/v1/documents",
      {
        method: "POST",
        body: formData,
      },
    );
  },

  // =====================================
  // REVIEW QUEUE
  // =====================================

  getQueuePage(
    status?: string,
    assignedTo?: string,
    limit = 20,
    offset = 0,
  ): Promise<PaginatedResponse<HumanReview>> {
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

    return requestWithHeaders<HumanReview[]>(
      `/api/v1/reviews/queue?${query.toString()}`,
    ).then(({ data, headers }) => {
      const total = readNumberHeader(
        headers,
        "X-Total-Count",
      );

      const hasMoreHeader = headers.get(
        "X-Has-More",
      );

      return {
        items: data,
        total,
        limit,
        offset,
        hasMore:
          hasMoreHeader === null
            ? null
            : hasMoreHeader === "true",
      };
    });
  },

  getReviewCount(
  status?: string,
): Promise<number | null> {
  return api.getQueuePage(
    status,
    undefined,
    1,
    0,
  ).then((result) => result.total);
},
  getQueue(
    status?: string,
    assignedTo?: string,
  ): Promise<HumanReview[]> {
    return this.getQueuePage(
      status,
      assignedTo,
      100,
      0,
    ).then((result) => result.items);
  },

  // =====================================
  // ACTION RECOVERY
  // =====================================

  getRecoveryQueue(
    limit = 100,
    offset = 0,
  ): Promise<ActionExecution[]> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request<ActionExecution[]>(
      `/api/v1/actions/recovery/queue?${query.toString()}`,
    );
  },

  // =====================================
  // EXTRACTION
  // =====================================

  runExtraction(
    documentId: number,
  ) {
    return request(
      `/api/v1/documents/${documentId}/extract`,
      { method: "POST" },
    );
  },

  getExtraction(
    documentId: number,
  ): Promise<ExtractionResult> {
    return request<ExtractionResult>(
      `/api/v1/documents/${documentId}/extraction`,
    );
  },

  // =====================================
  // BUSINESS EVALUATION
  // =====================================

  evaluateDocument(
    documentId: number,
  ) {
    return request(
      `/api/v1/documents/${documentId}/evaluate`,
      { method: "POST" },
    );
  },

  getEvaluation(
    documentId: number,
  ): Promise<BusinessEvaluation> {
    return request<BusinessEvaluation>(
      `/api/v1/documents/${documentId}/evaluation`,
    );
  },

  // =====================================
  // WORKFLOWS
  // =====================================

  startWorkflow(
    documentId: number,
  ) {
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
  ) {
    return request(
      `/api/v1/documents/${documentId}/workflow`,
    );
  },

  getWorkflow(
    workflowId: number,
  ): Promise<WorkflowRun> {
    return request<WorkflowRun>(
      `/api/v1/workflows/${workflowId}`,
    );
  },

  getWorkflows(
    status?: string,
    documentId?: number,
    limit = 20,
    offset = 0,
  ): Promise<PaginatedResponse<WorkflowRun>> {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    if (status) {
      query.set("status", status);
    }

    if (documentId !== undefined) {
      query.set("document_id", String(documentId));
    }

    return requestWithHeaders<WorkflowRun[]>(
      `/api/v1/workflows?${query.toString()}`,
    ).then(({ data, headers }) => {
      const total = readNumberHeader(
        headers,
        "X-Total-Count",
      );

      const hasMoreHeader = headers.get("X-Has-More");

      return {
        items: data,
        total,
        limit,
        offset,
        hasMore:
          hasMoreHeader === null
            ? null
            : hasMoreHeader === "true",
      };
    });
  },

  advanceWorkflow(
    workflowId: number,
  ) {
    return request(
      `/api/v1/workflows/${workflowId}/advance`,
      { method: "POST" },
    );
  },

  // =====================================
  // HUMAN REVIEW
  // =====================================

  createReview(
    workflowId: number,
  ): Promise<HumanReview> {
    return request<HumanReview>(
      `/api/v1/workflows/${workflowId}/review`,
      { method: "POST" },
    );
  },

  getReview(
    reviewId: number,
  ): Promise<HumanReview> {
    return request<HumanReview>(
      `/api/v1/reviews/${reviewId}`,
    );
  },

  assignReviewer(
    reviewId: number,
    reviewer: string,
  ): Promise<HumanReview> {
    return request<HumanReview>(
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
    return request<HumanReview>(
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
    return request<HumanReview>(
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
    return request<HumanReview>(
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
    return request<HumanReview>(
      `/api/v1/reviews/${reviewId}/reject`,
      {
        method: "POST",
        body: jsonBody({ note }),
      },
    );
  },

  // =====================================
  // ACTIONS
  // =====================================

  executeAction(
    reviewId: number,
    payload: {
      action_type: ActionType;
      recipient?: string;
      subject?: string;
      message?: string;
    },
  ): Promise<ActionExecution> {
    return request<ActionExecution>(
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

  getAction(actionId: number): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/actions/${actionId}`,
    );
  },

  retryAction(actionId: number): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/actions/${actionId}/retry`,
      { method: "POST" },
    );
  },

  // =====================================
    // AUDIT EVENTS
    // =====================================

    getAuditEvents(
      filters: AuditEventFilters = {},
    ): Promise<PaginatedResponse<AuditEvent>> {
      const query = new URLSearchParams();

      query.set("limit", String(filters.limit ?? 50));
      query.set("offset", String(filters.offset ?? 0));

      if (filters.event_type) {
        query.set("event_type", filters.event_type);
      }

      if (filters.entity_type) {
        query.set("entity_type", filters.entity_type);
      }

      if (filters.actor_id) {
        query.set("actor_id", filters.actor_id);
      }

      if (filters.document_id !== undefined) {
        query.set("document_id", String(filters.document_id));
      }

      if (filters.workflow_run_id !== undefined) {
        query.set(
          "workflow_run_id",
          String(filters.workflow_run_id),
        );
      }

      if (filters.review_id !== undefined) {
        query.set("review_id", String(filters.review_id));
      }

      if (filters.action_id !== undefined) {
        query.set("action_id", String(filters.action_id));
      }

      if (filters.search) {
        query.set("search", filters.search);
      }

      if (filters.from_datetime) {
        query.set("from_datetime", filters.from_datetime);
      }

      if (filters.to_datetime) {
        query.set("to_datetime", filters.to_datetime);
      }

      const limit = filters.limit ?? 50;
      const offset = filters.offset ?? 0;

      return requestWithHeaders<AuditEvent[]>(
        `/api/v1/audit/events?${query.toString()}`,
      ).then(({ data, headers }) => {
        const total = readNumberHeader(
          headers,
          "X-Total-Count",
        );

        const hasMoreHeader = headers.get("X-Has-More");

        return {
          items: data,
          total,
          limit,
          offset,
          hasMore:
            hasMoreHeader === null
              ? null
              : hasMoreHeader === "true",
        };
      });
    },
};