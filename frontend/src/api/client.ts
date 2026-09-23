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

async function request<T>(path: string, opts: RequestOption = {}): Promise<T>{
  const res = await fetch(
    path,
    {
      method: opts.method ?? "GET",
      headers: opts.body ? { "Content-Type": "application/json" } : undefined,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      credentials: "include",
      signal: opts.signal,
    }
  );
  if (res.status == 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const detail = (data && (data.detail ?? data.message)) || `HTTP ${res.status}`;
    throw new ApiError(res.status, detail);
  }
  return data as T;

}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body })
};
