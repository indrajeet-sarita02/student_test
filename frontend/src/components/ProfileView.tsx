"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { useToast } from "@/components/Toast";
import { formatDateTime, humanize } from "@/lib/utils";
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  Input,
  LoadingBlock,
  PageHeader,
  StatusBadge,
} from "@/components/ui";

export function ProfileView() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  if (!user) return <LoadingBlock />;

  const displayName =
    [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;

  const onChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (next.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (next !== confirm) {
      setError("New passwords do not match.");
      return;
    }
    setSaving(true);
    try {
      await authApi.changePassword(current, next);
      toast.success("Password updated successfully.");
      setCurrent("");
      setNext("");
      setConfirm("");
      await refreshUser();
    } catch (err) {
      setError(isApiError(err) ? err.message : "Unable to change password.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Profile" description="Your account details and security settings." />

      <Card>
        <CardHeader title="Account" />
        <CardBody className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">
              {displayName.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-base font-semibold text-slate-900">{displayName}</p>
              <p className="truncate text-sm text-slate-500">{user.email}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {user.roles.map((r) => (
                  <Badge key={r.id} tone="indigo">
                    {r.name}
                  </Badge>
                ))}
                <StatusBadge status={user.status} />
              </div>
            </div>
          </div>

          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase text-slate-400">Username</dt>
              <dd className="text-sm text-slate-800">{user.username}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Mobile</dt>
              <dd className="text-sm text-slate-800">{user.mobile ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Verified</dt>
              <dd className="text-sm text-slate-800">{user.is_verified ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Last login</dt>
              <dd className="text-sm text-slate-800">{formatDateTime(user.last_login_at)}</dd>
            </div>
          </dl>

          {user.student_profile && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="mb-2 text-xs font-semibold uppercase text-slate-400">
                Student profile
              </p>
              <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {Object.entries(user.student_profile)
                  .filter(([k]) => !["id", "user_id", "created_at", "updated_at"].includes(k))
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-[11px] uppercase text-slate-400">{humanize(k)}</dt>
                      <dd className="text-sm text-slate-800">
                        {v === null || v === undefined || v === "" ? "—" : String(v)}
                      </dd>
                    </div>
                  ))}
              </dl>
            </div>
          )}
        </CardBody>
      </Card>

      <Card className="mt-5">
        <CardHeader title="Change password" />
        <CardBody>
          <form onSubmit={onChangePassword} className="max-w-md space-y-4">
            {error && <Alert tone="error">{error}</Alert>}
            <Input
              label="Current password"
              type="password"
              autoComplete="current-password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              required
            />
            <Input
              label="New password"
              type="password"
              autoComplete="new-password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              help="At least 8 characters."
              required
            />
            <Input
              label="Confirm new password"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
            <Button type="submit" loading={saving}>
              Update password
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
