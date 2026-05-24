const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function formatFieldErrors(body: Record<string, unknown>): string | null {
  const messages: string[] = [];
  for (const [field, value] of Object.entries(body)) {
    if (field === "detail" || field === "non_field_errors") continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        messages.push(`${field}: ${String(item)}`);
      }
    } else if (typeof value === "string") {
      messages.push(`${field}: ${value}`);
    }
  }
  if (Array.isArray(body.non_field_errors)) {
    for (const item of body.non_field_errors) {
      messages.push(String(item));
    }
  }
  return messages.length > 0 ? messages.join(" ") : null;
}

function errorMessageFromBody(body: unknown, statusText: string): string {
  if (typeof body === "object" && body !== null) {
    const record = body as Record<string, unknown>;
    if ("detail" in record) {
      const detail = record.detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) return detail.map(String).join(" ");
    }
    const fieldErrors = formatFieldErrors(record);
    if (fieldErrors) return fieldErrors;
  }
  if (typeof body === "string" && body.trim()) return body;
  return statusText || "Request failed";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);

  if (!headers.has("Content-Type") && rest.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers,
  });

  let body: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      errorMessageFromBody(body, response.statusText),
      response.status,
      body,
    );
  }

  return body as T;
}
