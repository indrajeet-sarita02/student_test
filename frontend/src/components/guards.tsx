"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { Spinner } from "@/components/ui";

function FullPageSpinner() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Spinner className="h-7 w-7 text-brand-600" />
    </div>
  );
}

export function RequireAuth({
  children,
  staffOnly = false,
}: {
  children: React.ReactNode;
  staffOnly?: boolean;
}) {
  const { user, loading, isStaff } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  // Signed-out users go to /login (remembering the target); authenticated
  // non-staff users hitting a staff-only area go to /403.
  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (staffOnly && !isStaff) router.replace("/403");
  }, [loading, user, isStaff, staffOnly, pathname, router]);

  if (loading || !user) return <FullPageSpinner />;
  if (staffOnly && !isStaff) return null;

  return <>{children}</>;
}

/**
 * Gate a subtree behind a permission (or any of a list of permissions).
 *
 * - No requirement configured → renders children.
 * - Signed out → redirects to /login.
 * - Signed in without the permission → redirects to /403.
 *
 * The backend enforces the same rule; this only shapes the UI.
 */
export function RequirePermission({
  permission,
  anyOf,
  children,
}: {
  permission?: string;
  anyOf?: string[];
  children: React.ReactNode;
}) {
  const { user, loading, hasPermission } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const required = [
    ...(permission ? [permission] : []),
    ...(anyOf ?? []),
  ];
  const allowed = required.length === 0 || required.some((code) => hasPermission(code));

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (!allowed) router.replace("/403");
  }, [loading, user, allowed, pathname, router]);

  if (loading || !user) return <FullPageSpinner />;
  if (!allowed) return null;

  return <>{children}</>;
}
