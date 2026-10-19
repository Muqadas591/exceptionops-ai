import type {
  ActionExecution,
  ActionRequest,
  AuthTokens,
  BusinessEvaluation,
  HumanReview,
  ExtractionResult,
  WorkflowRun,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

type AuthRole = "reviewer" | "action";

interface RequestOptions extends RequestInit {
  auth?: AuthRole;
  tokens?: AuthTokens;
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth, tokens, ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers);

  if (fetchOptions.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (auth === "reviewer") {
    if (!tokens?.reviewerToken.trim()) {
      throw new Error("Enter the reviewer token first.");
    }

    headers.set("X-Reviewer-Token", tokens.reviewerToken.trim());
  }

  if (auth === "action") {
    if (!tokens?.actionToken.trim()) {
      throw new Error("Enter the action-operator token first.");
    }

    headers.set("X-Action-Token", tokens.actionToken.trim());
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchOptions,
    headers,
  });

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
      const detail = (data as { detail: unknown }).detail;
      message =
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail);
    } else if (typeof data === "string" && data) {
      message = data;
    }

    throw new Error(message);
  }

  return data as T;
}

function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}

export const api = {
  getQueue(
    tokens: AuthTokens,
    status?: string,
    assignedTo?: string,
  ): Promise<HumanReview[]> {
    const query = new URLSearchParams();

    if (status) query.set("status", status);
    if (assignedTo) query.set("assigned_to", assignedTo);

    const suffix = query.size ? `?${query.toString()}` : "";

    return request(`/api/v1/reviews/queue${suffix}`, {
      auth: "reviewer",
      tokens,
    });
  },

  createReview(
    workflowId: number,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/workflows/${workflowId}/review`, {
      method: "POST",
      auth: "reviewer",
      tokens,
    });
  },

  getReview(
    reviewId: number,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/reviews/${reviewId}`, {
      auth: "reviewer",
      tokens,
    });
  },

  getWorkflow(
    workflowId: number,
    tokens: AuthTokens,
  ): Promise<WorkflowRun> {
    return request(`/api/v1/workflows/${workflowId}`, {
      auth: "reviewer",
      tokens,
    });
  },

  getExtraction(
    documentId: number,
    tokens: AuthTokens,
  ): Promise<ExtractionResult> {
    return request(
      `/api/v1/documents/${documentId}/extraction`,
      { auth: "reviewer", tokens },
    );
  },

  getEvaluation(
    documentId: number,
    tokens: AuthTokens,
  ): Promise<BusinessEvaluation> {
    return request(
      `/api/v1/documents/${documentId}/evaluation`,
      { auth: "reviewer", tokens },
    );
  },

  assignReviewer(
    reviewId: number,
    reviewer: string,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/reviews/${reviewId}/assign`, {
      method: "POST",
      auth: "reviewer",
      tokens,
      body: jsonBody({ reviewer }),
    });
  },

  addComment(
    reviewId: number,
    body: string,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/reviews/${reviewId}/comments`, {
      method: "POST",
      auth: "reviewer",
      tokens,
      body: jsonBody({ body }),
    });
  },

  requestCorrection(
    reviewId: number,
    instructions: string,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}/request-correction`,
      {
        method: "POST",
        auth: "reviewer",
        tokens,
        body: jsonBody({ instructions }),
      },
    );
  },

  approveReview(
    reviewId: number,
    note: string,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/reviews/${reviewId}/approve`, {
      method: "POST",
      auth: "reviewer",
      tokens,
      body: jsonBody({ note }),
    });
  },

  rejectReview(
    reviewId: number,
    note: string,
    tokens: AuthTokens,
  ): Promise<HumanReview> {
    return request(`/api/v1/reviews/${reviewId}/reject`, {
      method: "POST",
      auth: "reviewer",
      tokens,
      body: jsonBody({ note }),
    });
  },

  executeAction(
    reviewId: number,
    payload: ActionRequest,
    tokens: AuthTokens,
  ): Promise<ActionExecution> {
    return request(`/api/v1/reviews/${reviewId}/actions`, {
      method: "POST",
      auth: "action",
      tokens,
      body: jsonBody(payload),
    });
  },

  getAction(
    actionId: number,
    tokens: AuthTokens,
  ): Promise<ActionExecution> {
    return request(`/api/v1/actions/${actionId}`, {
      auth: "action",
      tokens,
    });
  },

  retryAction(
    actionId: number,
    tokens: AuthTokens,
  ): Promise<ActionExecution> {
    return request(`/api/v1/actions/${actionId}/retry`, {
      method: "POST",
      auth: "action",
      tokens,
    });
  },
};