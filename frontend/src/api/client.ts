type HttpMethod = "GET" | "POST";

interface RequestOption{
  method?: HttpMethod;
  body?: unknown;
  signal?: AbortSignal;
}

export class ApiError extends Error{
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, opts: RequestOption = {}): Promise<T> {

  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers: opts.body ? { "Content-Type": "application/json" } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: "include",
    signal: opts.signal,
  });

  if (res.status === 204) return undefined as T;

  const text = await res.text();

  // Safely parse — non-JSON bodies (HTML error pages, plain text) must not
  // throw a raw SyntaxError; surface them as a proper ApiError instead.
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // Body is not valid JSON (e.g. uvicorn HTML 500, reverse-proxy page).
    throw new ApiError(res.status, `HTTP ${res.status}`);
  }

  if (!res.ok) {
    const rec = data as Record<string, unknown> | null;
    const detail = (rec && String(rec.detail ?? rec.message ?? "")) || `HTTP ${res.status}`;
    throw new ApiError(res.status, detail);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body })
};
