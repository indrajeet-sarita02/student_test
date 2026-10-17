"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui";

export default function ForbiddenPage() {
  const { user } = useAuth();

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 text-center">
      <h1 className="text-6xl font-extrabold text-brand-700">403</h1>
      <h2 className="mt-3 text-2xl font-semibold text-slate-900">
        Access denied
      </h2>
      <p className="mt-2 max-w-md text-sm text-slate-600">
        {user
          ? "You do not have the permissions required to view this page. Contact an administrator if you believe this is an error."
          : "This page is restricted. Please sign in to continue."}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Link href="/">
          <Button variant="outline">Go to home</Button>
        </Link>
        {!user && (
          <Link href="/login">
            <Button>Sign in</Button>
          </Link>
        )}
      </div>
    </div>
  );
}
