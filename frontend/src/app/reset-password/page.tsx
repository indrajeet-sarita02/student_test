"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { authApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import { Alert, Button, Card, Input } from "@/components/ui";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("token");
    if (t) setToken(t);
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.resetPassword(token.trim(), password);
      setDone(true);
      setTimeout(() => router.replace("/login"), 1500);
    } catch (err) {
      setError(isApiError(err) ? err.message : "Unable to reset password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-slate-100 px-4 py-10">
      <div className="w-full max-w-md">
        <h1 className="mb-1 text-center text-xl font-bold text-slate-900">Reset password</h1>
        <p className="mb-6 text-center text-sm text-slate-500">Choose a new password.</p>
        <Card className="p-5 sm:p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            {error && <Alert tone="error">{error}</Alert>}
            {done && <Alert tone="success">Password updated. Redirecting to sign in…</Alert>}
            <Input
              label="Reset token"
              name="token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
            <Input
              label="New password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              help="At least 8 characters."
              required
            />
            <Input
              label="Confirm password"
              name="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
            <Button type="submit" className="w-full" loading={submitting} disabled={done}>
              Reset password
            </Button>
          </form>
        </Card>
        <p className="mt-4 text-center text-sm">
          <Link href="/login" className="font-medium text-brand-600 hover:underline">
            ← Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
