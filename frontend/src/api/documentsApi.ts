import type {
  DocumentListParams,
  DocumentRecord,
} from "../types/document";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const AUTH_STORAGE_KEY = "exceptionops_access_token";

function getAccessToken(): string {
  const token = sessionStorage.getItem(AUTH_STORAGE_KEY);

  if (!token) {
    throw new Error(
      "Your login session is missing. Please sign in again.",
    );
  }

  return token;
}

function getAuthHeaders(): Headers {
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${getAccessToken()}`);
  return headers;
}

async function parseError(response: Response): Promise<string> {
  const responseText = await response.text();

  if (!responseText) {
    return `Request failed with status ${response.status}.`;
  }

  try {
    const data: unknown = JSON.parse(responseText);

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

      if (detail && typeof detail === "object") {
        return JSON.stringify(detail);
      }
    }

    return JSON.stringify(data);
  } catch {
    return responseText;
  }
}

async function handleResponse<T>(
  response: Response,
): Promise<T> {
  if (response.status === 401) {
    window.dispatchEvent(
      new Event("session-expired"),
    );

    throw new Error(
      "Your session has expired. Please sign in again.",
    );
  }

  if (!response.ok) {
    const message = await parseError(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function getDocuments(
  params: DocumentListParams = {},
): Promise<DocumentRecord[]> {
  const query = new URLSearchParams();

  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));

  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents?${query.toString()}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    },
  );

  return handleResponse<DocumentRecord[]>(response);
}

export async function getDocument(
  documentId: number,
): Promise<DocumentRecord> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/${documentId}`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    },
  );

  return handleResponse<DocumentRecord>(response);
}

export async function uploadDocument(
  file: File,
): Promise<DocumentRecord> {
  const formData = new FormData();

  // The backend expects the field name to be exactly "file".
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents`,
    {
      method: "POST",
      headers: getAuthHeaders(),

      // Do not set Content-Type here.
      // The browser adds multipart/form-data and its boundary.
      body: formData,
    },
  );

  return handleResponse<DocumentRecord>(response);
}

export async function downloadDocument(
  documentId: number,
  originalFilename: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/${documentId}/content`,
    {
      method: "GET",
      headers: getAuthHeaders(),
    },
  );

  if (response.status === 401) {
    window.dispatchEvent(
      new Event("session-expired"),
    );

    throw new Error(
      "Your session has expired. Please sign in again.",
    );
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);

  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = originalFilename;

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(objectUrl);
}