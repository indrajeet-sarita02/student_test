import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Server-side route protection. Permission (RBAC) checks stay on the client via
// `RequirePermission`, because permissions are not available until /auth/me
// resolves — the backend remains authoritative either way.
//
// The access token is mirrored into a first-party cookie by `tokenStore`, so
// this middleware can gate direct navigations before React hydrates.

// Routes reachable without a session.
const PUBLIC_ROUTES = ["/login", "/forgot-password", "/reset-password", "/403"];

const SESSION_COOKIE = "st_access_token";

function isPublic(pathname: string): boolean {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(SESSION_COOKIE)?.value);

  // Signed-in users don't need the login screen again.
  if (pathname === "/login" && hasSession) {
    const next = request.nextUrl.searchParams.get("next");
    const target = next && next.startsWith("/") ? next : "/";
    return NextResponse.redirect(new URL(target, request.url));
  }

  if (isPublic(pathname)) return NextResponse.next();

  if (!hasSession) {
    const login = new URL("/login", request.url);
    // Preserve the intended destination across the redirect.
    login.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  // Skip API routes, Next internals and files with an extension.
  matcher: ["/((?!api/|_next/|.*\\..*).*)"],
};
