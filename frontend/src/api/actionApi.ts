import type {
  ActionExecution,
  CreateActionRequest,
  ReconcileActionRequest,
} from "../types/action";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const AUTH_STORAGE_KEY = "exceptionops_access_token";

export class ActionApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ActionApiError";
    this.statusCode = statusCode;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = sessionStorage.getItem(AUTH_STORAGE_KEY);

  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    window.dispatchEvent(new Event("session-expired"));
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail ?? data);
    } catch {
      // Keep the fallback error message.
    }

    throw new ActionApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const actionsApi = {
  createForReview(
    reviewId: number,
    payload: CreateActionRequest,
    idempotencyKey: string,
  ): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/reviews/${reviewId}/actions`,
      {
        method: "POST",
        headers: {
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(payload),
      },
    );
  },

  getAction(actionId: number): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/actions/${actionId}`,
    );
  },

  getReviewActions(
    reviewId: number,
    limit = 20,
    offset = 0,
  ): Promise<ActionExecution[]> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request<ActionExecution[]>(
      `/api/v1/reviews/${reviewId}/actions?${params}`,
    );
  },

  getRecoveryQueue(
    limit = 50,
    offset = 0,
  ): Promise<ActionExecution[]> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    return request<ActionExecution[]>(
      `/api/v1/actions/recovery/queue?${params}`,
    );
  },

  retry(actionId: number): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/actions/${actionId}/retry`,
      { method: "POST" },
    );
  },

  reconcile(
    actionId: number,
    payload: ReconcileActionRequest,
  ): Promise<ActionExecution> {
    return request<ActionExecution>(
      `/api/v1/actions/${actionId}/reconcile`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },
};