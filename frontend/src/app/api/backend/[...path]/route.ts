import { NextRequest } from "next/server";

// Server-side backend origin. Overridable via env; the browser never sees it.
const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

// This proxy exists so the browser talks ONLY to the same origin (no CORS) and
// so trailing slashes survive. A plain Next `rewrite` drops the trailing slash
// from `/api/backend/exams/` -> the FastAPI backend then 307-redirects to an
// absolute backend URL and the browser drops the Authorization header
// (-> "Authentication credentials were not provided"). Handling the proxy in a
// route handler preserves the exact path, method, headers and body.
export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";
export const runtime = "nodejs";

// The backend uses a single slow worker; its keep-alive timeout is 5s and the
// client pool can occasionally race a just-closed socket. Retrying (the request
// body is buffered below, so this is safe for every method) removes those
// intermittent 502s / "Unable to reach the server" errors.
const MAX_ATTEMPTS = 3;
const UPSTREAM_TIMEOUT_MS = 60000;

// Hop-by-hop / problematic headers we must not forward verbatim.
const STRIP_REQUEST_HEADERS = new Set([
  "host",
  "connection",
  "content-length",
  "transfer-encoding",
  "keep-alive",
  "upgrade",
  "proxy-authorization",
  "te",
  "trailer",
  // Let Node negotiate and decompress the response itself.
  "accept-encoding",
  // The access token is mirrored into this cookie for the fallback below; it
  // must not be forwarded to the backend as a cookie.
  "cookie",
]);

const STRIP_RESPONSE_HEADERS = new Set([
  "content-encoding",
  "content-length",
  "transfer-encoding",
  "connection",
  "keep-alive",
]);

function targetUrl(req: NextRequest): string {
  const pathname = req.nextUrl.pathname.replace(/^\/api\/backend/, "");
  const suffix = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return `${BACKEND_URL}/api/v1${suffix}${req.nextUrl.search}`;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchUpstream(
  url: string,
  method: string,
  headers: Headers,
  body: ArrayBuffer | undefined,
): Promise<{ status: number; headers: Headers; bytes: ArrayBuffer }> {
  let lastError: unknown;
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);
    try {
      const res = await fetch(url, {
        method,
        headers,
        body,
        redirect: "manual",
        cache: "no-store",
        signal: controller.signal,
      });
      const bytes = await res.arrayBuffer();
      return { status: res.status, headers: res.headers, bytes };
    } catch (err) {
      lastError = err;
    } finally {
      clearTimeout(timer);
    }
    if (attempt < MAX_ATTEMPTS - 1) await sleep(150 * (attempt + 1));
  }
  throw lastError;
}

async function proxy(req: NextRequest): Promise<Response> {
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (!STRIP_REQUEST_HEADERS.has(key.toLowerCase())) headers.set(key, value);
  });

  // Fallback: if the caller did not send an Authorization header, build one
  // from the first-party token cookie the frontend sets at login. This keeps
  // direct navigations and "Copy as cURL" requests authenticated.
  if (!headers.has("authorization")) {
    const cookieToken = req.cookies.get("st_access_token")?.value;
    if (cookieToken) headers.set("authorization", `Bearer ${cookieToken}`);
  }

  const method = req.method.toUpperCase();
  const hasBody = !["GET", "HEAD"].includes(method);

  let body: ArrayBuffer | undefined;
  if (hasBody) {
    const buf = await req.arrayBuffer();
    if (buf.byteLength > 0) body = buf;
  }

  let upstreamRes: { status: number; headers: Headers; bytes: ArrayBuffer };
  try {
    upstreamRes = await fetchUpstream(targetUrl(req), method, headers, body);
  } catch {
    return Response.json(
      { success: false, error: { code: "PROXY_ERROR", message: "Backend is unreachable." } },
      { status: 502 },
    );
  }

  const resHeaders = new Headers();
  upstreamRes.headers.forEach((value, key) => {
    if (STRIP_RESPONSE_HEADERS.has(key.toLowerCase())) return;
    // Keep redirects same-origin so the browser stays on the proxy and keeps
    // sending the Authorization header.
    if (key.toLowerCase() === "location") {
      resHeaders.set(key, value.replace(`${BACKEND_URL}/api/v1`, "/api/backend"));
      return;
    }
    resHeaders.set(key, value);
  });

  const { status, bytes } = upstreamRes;
  if (status === 204 || status === 304 || method === "HEAD") {
    return new Response(null, { status, headers: resHeaders });
  }

  return new Response(upstreamRes.bytes, { status, headers: resHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
export const OPTIONS = proxy;
