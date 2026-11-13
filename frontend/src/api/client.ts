/**
 * Minimal HTTP client for the JobPilot API.
 * - Session lives in httpOnly cookies (never readable from JS).
 * - Unsafe requests echo the `csrf_token` cookie in the X-CSRF-Token header.
 * - A 401 triggers one silent refresh attempt, then the request is retried.
 */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: { field: string; message: string }[],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
const NO_REFRESH_PATHS = ['/auth/login', '/auth/refresh', '/auth/register'];

export function readCookie(name: string): string | undefined {
  return document.cookie
    .split('; ')
    .find((c) => c.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

let refreshing: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  // Concurrent 401s share a single refresh request.
  refreshing ??= rawRequest('/auth/refresh', { method: 'POST' })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

function rawRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const method = (init.method ?? 'GET').toUpperCase();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (!SAFE_METHODS.has(method)) {
    const csrf = readCookie('csrf_token');
    if (csrf) headers.set('X-CSRF-Token', csrf);
  }
  return fetch(`/api${path}`, { ...init, method, headers, credentials: 'include' });
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as {
      error?: { code: string; message: string; details?: { field: string; message: string }[] };
    };
    if (body.error) {
      return new ApiError(response.status, body.error.code, body.error.message, body.error.details);
    }
  } catch {
    // non-JSON error body
  }
  return new ApiError(response.status, `http_${response.status}`, response.statusText);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response = await rawRequest(path, init);
  if (response.status === 401 && !NO_REFRESH_PATHS.includes(path)) {
    if (await refreshSession()) response = await rawRequest(path, init);
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const json = (data: unknown): RequestInit => ({ body: JSON.stringify(data) });
