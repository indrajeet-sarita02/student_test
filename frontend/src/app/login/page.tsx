"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/auth-context";
import { landingPathFor } from "@/lib/permissions";
import { isApiError } from "@/lib/api/client";
import { Alert, Button, Card, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace(landingPathFor(user.roles?.map((r) => r.code)));
    }
  }, [loading, user, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const me = await login(username.trim(), password);
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next");
      const target = next || landingPathFor(me.roles?.map((r) => r.code));
      router.replace(target);
    } catch (err) {
      setError(
        isApiError(err) ? err.message : "Unable to sign in. Please try again."
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-slate-100 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-2xl text-white shadow-md">
            🎯
          </div>
          <h1 className="text-xl font-bold text-slate-900">Student Test Platform</h1>
          <p className="mt-1 text-sm text-slate-500">Sign in to continue</p>
        </div>

        <Card className="p-5 sm:p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            {error && <Alert tone="error">{error}</Alert>}
            <Input
              label="Username or Email"
              name="username"
              autoComplete="username"
              placeholder="admin or admin@example.com"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <div className="flex items-center justify-between text-sm">
              <Link href="/forgot-password" className="font-medium text-brand-600 hover:underline">
                Forgot password?
              </Link>
            </div>
            <Button type="submit" className="w-full" loading={submitting}>
              Sign in
            </Button>
          </form>
        </Card>

        <div className="mt-4 rounded-xl border border-slate-200 bg-white/70 p-3 text-xs text-slate-500">
          <p className="font-semibold text-slate-600">Demo accounts (password Admin@123)</p>
          <p className="mt-1">Admin: <span className="font-mono">admin</span> · Super admin: <span className="font-mono">superadmin@example.com</span> · Student: <span className="font-mono">student@example.com</span></p>
        </div>
      </div>
    </div>
  );
}
