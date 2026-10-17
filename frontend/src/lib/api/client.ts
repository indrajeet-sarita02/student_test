"use client";

// Normalised API client for the FastAPI backend.
//
// - Attaches the bearer access token.
// - On 401 it tries a one-shot refresh (shared across concurrent requests)
//   and retries the original request.
// - Normalises the backend error envelope:
//     { success: false, error: { code, message, details } }
// - Exposes a `download` helper for CSV/streamed exports.

import type { ApiErrorShape, TokenResponse } from "@/lib/types";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/api/backend";

const ACCESS_KEY = "st_access_token";
const REFRESH_KEY = "st_refresh_token";

export class ApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(message: string, code = "UNKNOWN", status = 0, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}

// ------------------------------------------------------------- token store
function safeGet(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

// Mirror the access token into a first-party cookie so the server-side proxy
// (`/api/backend/*`) can attach the `Authorization: Bearer` header even when a
// request does not carry it (direct navigation, "Copy as cURL", form posts).
function setCookie(name: string, value: string) {
  if (typeof document === "undefined") return;
  try {
    document.cookie = `${name}=${encodeURIComponent(value)}; path=/; SameSite=Lax`;
  } catch {
    /* ignore */
  }
}

function clearCookie(name: string) {
  if (typeof document === "undefined") return;
  try {
    document.cookie = `${name}=; path=/; Max-Age=0; SameSite=Lax`;
  } catch {
    /* ignore */
  }
}

export const tokenStore = {
  getAccess: () => safeGet(ACCESS_KEY),
  getRefresh: () => safeGet(REFRESH_KEY),
  set(tokens: TokenResponse | null) {
    safeSet(ACCESS_KEY, tokens ? tokens.access_token : null);
    safeSet(REFRESH_KEY, tokens ? tokens.refresh_token : null);
    if (tokens) setCookie(ACCESS_KEY, tokens.access_token);
    else clearCookie(ACCESS_KEY);
  },
  clear() {
    safeSet(ACCESS_KEY, null);
    safeSet(REFRESH_KEY, null);
    clearCookie(ACCESS_KEY);
  },
  /** Ensure the cookie mirrors the current access token (e.g. sessions that
   *  existed before the cookie fallback was added). */
  mirrorCookie() {
    const token = safeGet(ACCESS_KEY);
    if (token) setCookie(ACCESS_KEY, token);
    else clearCookie(ACCESS_KEY);
  },
};

// ------------------------------------------------------------- 401 handling
type UnauthorizedHandler = () => void;
let onUnauthorized: UnauthorizedHandler | null = null;
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  onUnauthorized = handler;
}

let refreshPromise: Promise<boolean> | null = null;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Methods that are safe to replay when the connection fails before a response
// is received (e.g. a keep-alive socket the dev server just closed). POST/PATCH
// are intentionally excluded so a create/update is never duplicated.
const RETRYABLE_METHODS = new Set(["GET", "HEAD", "PUT", "DELETE", "OPTIONS"]);
const NETWORK_MAX_ATTEMPTS = 3;

//: Hard cap on a single API round-trip (including its network retries).
const REQUEST_TIMEOUT_MS = 30000;

/** fetch() with a couple of retries for transient network-level failures. */
async function fetchWithRetry(
  url: string,
  init: RequestInit,
  method: string
): Promise<Response> {
  const attempts = RETRYABLE_METHODS.has(method.toUpperCase()) ? NETWORK_MAX_ATTEMPTS : 1;
  const idempotent = RETRYABLE_METHODS.has(method.toUpperCase());
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      const res = await fetch(url, init);
      // Retry transient gateway errors (the proxy returns 502/503/504 while the
      // backend is restarting or briefly overloaded) for idempotent requests.
      if (idempotent && (res.status === 502 || res.status === 503 || res.status === 504) && attempt < attempts - 1) {
        await sleep(300 * (attempt + 1));
        continue;
      }
      return res;
    } catch (err) {
      // A deliberate abort must surface untouched.
      if ((err as Error)?.name === "AbortError") throw err;
      lastError = err;
      if (attempt < attempts - 1) await sleep(200 * (attempt + 1));
    }
  }
  throw lastError;
}

// Returns true when the session was refreshed, false when the refresh token is
// rejected. Throws ApiError(NETWORK_ERROR) when the refresh endpoint itself
// could not be reached — callers must NOT clear tokens in that case.
async function refreshTokens(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;
  let res: Response;
  try {
    res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
  } catch (err) {
    if ((err as Error)?.name === "AbortError") throw err;
    throw new ApiError(
      "Unable to reach the server. Check your connection and try again.",
      "NETWORK_ERROR",
      0
    );
  }
  if (!res.ok) return false;
  const data = (await res.json()) as TokenResponse;
  tokenStore.set(data);
  return true;
}

function ensureRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshTokens().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

// ------------------------------------------------------------- core request
interface RequestOptions {
  skipAuth?: boolean;
  skipRefresh?: boolean;
  raw?: boolean;
  signal?: AbortSignal;
}

async function parseError(res: Response): Promise<ApiError> {
  let code = `HTTP_${res.status}`;
  let message = res.statusText || "Request failed";
  let details: unknown;
  try {
    const body = (await res.json()) as ApiErrorShape | { detail?: unknown };
    if (body && typeof body === "object" && "error" in body && body.error) {
      code = body.error.code || code;
      message = body.error.message || message;
      details = body.error.details;
    } else if (body && typeof body === "object" && "detail" in body) {
      // FastAPI validation error
      code = "VALIDATION_ERROR";
      message = "The submitted data is invalid.";
      details = body.detail;
      if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg as string;
      }
    }
  } catch {
    /* non-JSON body */
  }
  return new ApiError(message, code, res.status, details);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";

  if (!options.skipAuth) {
    let token = tokenStore.getAccess();
    // If the access token is missing but a refresh token exists, establish a
    // session FIRST so a protected request is never sent without an
    // Authorization header (which the backend rejects with MISSING_TOKEN).
    if (!token && !options.skipRefresh) {
      let refreshed: boolean;
      try {
        refreshed = await ensureRefresh();
      } catch (err) {
        if ((err as Error)?.name === "AbortError") throw err;
        throw new ApiError(
          "Unable to reach the server. Check your connection and try again.",
          "NETWORK_ERROR",
          0
        );
      }
      if (refreshed) token = tokenStore.getAccess();
    }
    if (!token) {
      // No credentials at all — don't send a doomed unauthenticated request.
      onUnauthorized?.();
      throw new ApiError("Your session has expired. Please sign in again.", "UNAUTHORIZED", 401);
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let res: Response;
  let timedOut = false;
  const controller = options.signal ? null : new AbortController();
  const signal = options.signal ?? controller?.signal;
  const timer = controller
    ? setTimeout(() => {
        timedOut = true;
        controller.abort();
      }, REQUEST_TIMEOUT_MS)
    : null;
  try {
    res = await fetchWithRetry(
      `${BASE}${path}`,
      {
        method,
        headers,
        body:
          body === undefined
            ? undefined
            : isForm
            ? (body as FormData)
            : JSON.stringify(body),
        signal,
      },
      method
    );
  } catch (err) {
    if ((err as Error)?.name === "AbortError") {
      // A timeout surfaces as a friendly error; a caller-supplied abort does not.
      if (timedOut) {
        throw new ApiError("The request timed out. Please try again.", "TIMEOUT", 0);
      }
      throw err;
    }
    throw new ApiError(
      "Unable to reach the server. Check your connection and try again.",
      "NETWORK_ERROR",
      0
    );
  } finally {
    if (timer) clearTimeout(timer);
  }

  if (res.status === 401 && !options.skipAuth && !options.skipRefresh) {
    let refreshed: boolean;
    try {
      refreshed = await ensureRefresh();
    } catch (err) {
      // The refresh call could not reach the server — keep the tokens and let
      // the caller retry instead of logging the user out.
      if ((err as Error)?.name === "AbortError") throw err;
      throw new ApiError(
        "Unable to reach the server. Check your connection and try again.",
        "NETWORK_ERROR",
        0
      );
    }
    if (refreshed) {
      return request<T>(method, path, body, { ...options, skipRefresh: true });
    }
    tokenStore.clear();
    onUnauthorized?.();
    throw new ApiError("Your session has expired. Please sign in again.", "UNAUTHORIZED", 401);
  }

  if (!res.ok) throw await parseError(res);

  if (options.raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>("GET", path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, body, options),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PATCH", path, body, options),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>("DELETE", path, undefined, options),

  /** Fetch a binary export (CSV) with auth + refresh handling. */
  async download(path: string): Promise<Blob> {
    const token = tokenStore.getAccess();
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, REQUEST_TIMEOUT_MS);
    let res: Response;
    try {
      res = await fetchWithRetry(
        `${BASE}${path}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: controller.signal },
        "GET"
      );
    } catch (err) {
      if ((err as Error)?.name === "AbortError") {
        if (timedOut) {
          throw new ApiError("The request timed out. Please try again.", "TIMEOUT", 0);
        }
        throw err;
      }
      throw new ApiError(
        "Unable to reach the server. Check your connection and try again.",
        "NETWORK_ERROR",
        0
      );
    } finally {
      clearTimeout(timer);
    }
    if (res.status === 401) {
      const refreshed = await ensureRefresh();
      if (refreshed) {
        const retry = await fetchWithRetry(
          `${BASE}${path}`,
          { headers: { Authorization: `Bearer ${tokenStore.getAccess()}` } },
          "GET"
        );
        if (!retry.ok) throw await parseError(retry);
        return retry.blob();
      }
      onUnauthorized?.();
      throw new ApiError("Your session has expired.", "UNAUTHORIZED", 401);
    }
    if (!res.ok) throw await parseError(res);
    return res.blob();
  },
};

/** Build a query string, dropping empty/undefined values. */
export function qs(params: Record<string, unknown> = {}): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const str = search.toString();
  return str ? `?${str}` : "";
}
