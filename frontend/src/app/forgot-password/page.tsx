"use client";

import { useState } from "react";
import Link from "next/link";

import { authApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import { Alert, Button, Card, Input } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setResetToken(null);
    setSubmitting(true);
    try {
      const res = await authApi.forgotPassword(email.trim());
      setMessage(res.message || "If the account exists, a reset link has been sent.");
      if (res.reset_token) setResetToken(res.reset_token);
    } catch (err) {
      setError(isApiError(err) ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-slate-100 px-4 py-10">
      <div className="w-full max-w-md">
        <h1 className="mb-1 text-center text-xl font-bold text-slate-900">Forgot password</h1>
        <p className="mb-6 text-center text-sm text-slate-500">
          Enter your email and we&apos;ll send reset instructions.
        </p>
        <Card className="p-5 sm:p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            {error && <Alert tone="error">{error}</Alert>}
            {message && <Alert tone="success">{message}</Alert>}
            {resetToken && (
              <Alert tone="info">
                <p className="font-medium">Development reset token:</p>
                <code className="mt-1 block break-all rounded bg-white/60 p-2 text-xs">{resetToken}</code>
                <Link
                  href={`/reset-password?token=${encodeURIComponent(resetToken)}`}
                  className="mt-2 inline-block font-medium text-brand-700 hover:underline"
                >
                  Continue to reset →
                </Link>
              </Alert>
            )}
            <Input
              label="Email"
              name="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Button type="submit" className="w-full" loading={submitting}>
              Send reset link
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
