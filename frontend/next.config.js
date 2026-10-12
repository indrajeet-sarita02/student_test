/** @type {import('next').NextConfig} */

// The backend base URL (server-side only). The browser never talks to FastAPI
// directly; `/api/backend/*` is proxied by the route handler at
// `src/app/api/backend/[...path]/route.ts`, so CORS never applies.
// On Vercel, default to the deployed backend; override with BACKEND_URL.
const DEFAULT_BACKEND_URL = "https://student-testapi.vercel.app";
const BACKEND_URL = (
  process.env.BACKEND_URL ||
  (process.env.VERCEL ? DEFAULT_BACKEND_URL : "http://127.0.0.1:8000")
).replace(/\/$/, "");

const nextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  // IMPORTANT: without this, Next 308-redirects `/api/backend/exams/` to
  // `/api/backend/exams` before the proxy route handler runs. The trailing
  // slash is then lost, FastAPI 307-redirects to an ABSOLUTE backend URL, and
  // the browser follows it cross-origin, dropping the Authorization header
  // (-> "Authentication credentials were not provided"). Skipping Next's
  // trailing-slash redirect lets the handler receive the exact path.
  skipTrailingSlashRedirect: true,
  experimental: {
    // The catch-all proxy route is dynamic, so Next dev forks a short-lived
    // `jest-worker` child process per request to compute "static paths". On
    // memory-constrained machines those forks fail with `spawn ENOMEM`,
    // surfacing as 500s / "Unable to reach the server". Worker threads avoid
    // the fork and are much lighter.
    workerThreads: true,
  },
  async rewrites() {
    return [
      {
        source: "/favicon.ico",
        destination: "/icon.svg",
      },
      {
        source: "/api/health",
        destination: `${BACKEND_URL}/health`,
      },
    ];
  },
};

module.exports = nextConfig;
