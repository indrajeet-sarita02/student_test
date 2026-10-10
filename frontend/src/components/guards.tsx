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

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, user, pathname, router]);

  if (loading || !user) return <FullPageSpinner />;

  if (staffOnly && !isStaff) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <div className="text-4xl">⛔</div>
        <h2 className="mt-3 text-lg font-semibold text-slate-900">
          You do not have permission
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          This area is restricted to administrators.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
