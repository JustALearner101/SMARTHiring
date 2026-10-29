import { ApiError, apiFetch, type ApiRequestOptions } from "@/lib/api";
import type { ApiResponse } from "@/types/master";

export { ApiError };
export type { ApiRequestOptions };

export type QueryValue = string | number | boolean | null | undefined;

/**
 * Builds a query string (including the leading "?") and skips empty values.
 * Required because several FastAPI endpoints declare their payload as Query(...)
 * parameters rather than a JSON body.
 */
export function buildQuery(params: Record<string, QueryValue> = {}): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

/**
 * Calls apiFetch and unwraps the standard ApiResponse<T> envelope so services
 * return clean domain objects to the React layer.
 */
export async function request<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const payload = await apiFetch<ApiResponse<T>>(endpoint, options);
  if (payload !== null && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }
  return payload as unknown as T;
}

export function isNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function jsonPost(body: unknown): ApiRequestOptions {
  return { method: "POST", body: JSON.stringify(body) };
}

export function jsonPatch(body: unknown): ApiRequestOptions {
  return { method: "PATCH", body: JSON.stringify(body) };
}

export function jsonPut(body: unknown): ApiRequestOptions {
  return { method: "PUT", body: JSON.stringify(body) };
}

export function jsonDelete(): ApiRequestOptions {
  return { method: "DELETE" };
}
