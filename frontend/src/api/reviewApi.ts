import type {
  HumanReview,
  ReviewQueueResponse,
  ReviewStatusFilter,
} from "../types/review";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const AUTH_STORAGE_KEY = "exceptionops_access_token";

export class ReviewApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ReviewApiError";
    this.statusCode = statusCode;
  }
}

function authHeaders(): Headers {
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

async function readError(
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
  const headers = authHeaders();

  new Headers(options.headers).forEach((value, key) => {
    headers.set(key, value);
  });

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

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

    throw new ReviewApiError(
      "Your session has expired. Please sign in again.",
      401,
    );
  }

  if (!response.ok) {
    throw new ReviewApiError(
      await readError(response),
      response.status,
    );
  }

  return (await response.json()) as T;
}

function jsonBody(payload: unknown): string {
  return JSON.stringify(payload);
}

export const reviewsApi = {
  // --------------------------------
  // EXCEPTION QUEUE
  // --------------------------------

  async getQueue(params: {
    status?: ReviewStatusFilter;
    assignedTo?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ReviewQueueResponse> {
    const query = new URLSearchParams();

    if (params.status) {
      query.set("status", params.status);
    }

    if (params.assignedTo?.trim()) {
      query.set("assigned_to", params.assignedTo.trim());
    }

    query.set("limit", String(params.limit ?? 20));
    query.set("offset", String(params.offset ?? 0));

    const headers = authHeaders();

    const response = await fetch(
      `${API_BASE_URL}/api/v1/reviews/queue?${query}`,
      { headers },
    );

    if (response.status === 401) {
      window.dispatchEvent(
        new Event("session-expired"),
      );

      throw new ReviewApiError(
        "Your session has expired. Please sign in again.",
        401,
      );
    }

    if (!response.ok) {
      throw new ReviewApiError(
        await readError(response),
        response.status,
      );
    }

    const items =
      (await response.json()) as HumanReview[];

    const totalHeader = response.headers.get(
      "X-Total-Count",
    );

    const limitHeader = response.headers.get(
      "X-Page-Limit",
    );

    const offsetHeader = response.headers.get(
      "X-Page-Offset",
    );

    const moreHeader = response.headers.get(
      "X-Has-More",
    );

    return {
      items,
      total: Number(totalHeader ?? items.length),
      limit: Number(limitHeader ?? params.limit ?? 20),
      offset: Number(offsetHeader ?? params.offset ?? 0),
      hasMore: moreHeader === "true",
    };
  },

  // --------------------------------
  // CREATE / OPEN REVIEW
  // --------------------------------

  createReview(
    workflowId: number,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/workflows/${workflowId}/review`,
      { method: "POST" },
    );
  },

  // --------------------------------
  // REVIEW DETAILS
  // --------------------------------

  getReview(
    reviewId: number,
  ): Promise<HumanReview> {
    return request(
      `/api/v1/reviews/${reviewId}`,
    );
  },

  // --------------------------------
  // ASSIGN REVIEWER
  // --------------------------------

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

  // --------------------------------
  // ADD COMMENT
  // --------------------------------

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

  // --------------------------------
  // REQUEST CORRECTION
  // --------------------------------

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

  // --------------------------------
  // APPROVE
  // --------------------------------

  approve(
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

  // --------------------------------
  // REJECT
  // --------------------------------

  reject(
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
};