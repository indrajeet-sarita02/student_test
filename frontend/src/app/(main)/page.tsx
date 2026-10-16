"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth/auth-context";
import { notificationsApi, studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { formatDateTime, formatPercent } from "@/lib/utils";
import {
  Alert,
  Badge,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  LoadingBlock,
  PageHeader,
  StatCard,
  StatusBadge,
} from "@/components/ui";
import { StartTestButton } from "@/components/student/StartTestButton";

export default function DashboardPage() {
  const { user } = useAuth();
  const tests = useApi(() => studentApi.tests());
  const results = useApi(() => studentApi.results({ page: 1, page_size: 5 }));
  const notifications = useApi(() => notificationsApi.list({ page: 1, page_size: 5 }));

  const available = (tests.data ?? []).filter((t) => t.can_attempt);
  const inProgress = (tests.data ?? []).filter(
    (t) => t.last_attempt_status === "IN_PROGRESS" || t.last_attempt_status === "STARTED"
  );
  const best = (results.data?.items ?? []).reduce<number | null>(
    (acc, r) => (acc === null ? r.percentage : Math.max(acc, r.percentage)),
    null
  );

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.username || "there";

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${displayName}`}
        description="Here is an overview of your tests and results."
      />

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard label="Available tests" value={available.length} icon="🧪" />
        <StatCard
          label="Attempts"
          value={results.data?.total ?? 0}
          icon="⏱️"
          hint={`${inProgress.length} in progress`}
        />
        <StatCard label="Best score" value={formatPercent(best)} icon="🏆" />
        <StatCard
          label="Notifications"
          value={notifications.data?.total ?? 0}
          icon="🔔"
        />
      </div>

      {inProgress.length > 0 && (
        <Alert tone="warning" className="mt-4">
          You have {inProgress.length} test{inProgress.length > 1 ? "s" : ""} in progress.{" "}
          <Link href="/history" className="font-medium underline">
            Resume now →
          </Link>
        </Alert>
      )}

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Available tests"
            actions={
              <Link href="/tests" className="text-xs font-medium text-brand-600 hover:underline">
                View all
              </Link>
            }
          />
          {tests.loading ? (
            <LoadingBlock />
          ) : tests.error ? (
            <div className="px-4 py-6 text-sm text-rose-600">{tests.error}</div>
          ) : available.length === 0 ? (
            <EmptyState title="No tests available" description="Check back later for assigned tests." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {available.slice(0, 5).map((item) => (
                <li
                  key={item.assignment_id}
                  className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">
                      {item.test.name}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {item.test.duration_minutes} min · {item.test.total_marks} marks ·{" "}
                      {item.attempts_remaining} attempt(s) left
                    </p>
                  </div>
                  <StartTestButton testId={item.test.id} />
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-5">
          <Card>
            <CardHeader
              title="Recent results"
              actions={
                <Link href="/results" className="text-xs font-medium text-brand-600 hover:underline">
                  View all
                </Link>
              }
            />
            {results.loading ? (
              <LoadingBlock />
            ) : (results.data?.items ?? []).length === 0 ? (
              <EmptyState title="No results yet" icon="📊" />
            ) : (
              <ul className="divide-y divide-slate-100">
                {results.data!.items.map((r) => (
                  <li key={r.id} className="flex items-center justify-between gap-2 px-4 py-2.5">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-800">{r.test_name}</p>
                      <p className="text-xs text-slate-500">{formatDateTime(r.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-800">
                        {formatPercent(r.percentage)}
                      </span>
                      <Badge tone={r.pass_status ? "green" : "red"}>
                        {r.pass_status ? "Pass" : "Fail"}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardHeader
              title="Notifications"
              actions={
                <Link
                  href="/notifications"
                  className="text-xs font-medium text-brand-600 hover:underline"
                >
                  View all
                </Link>
              }
            />
            {notifications.loading ? (
              <LoadingBlock />
            ) : (notifications.data?.items ?? []).length === 0 ? (
              <EmptyState title="No notifications" icon="🔔" />
            ) : (
              <ul className="divide-y divide-slate-100">
                {notifications.data!.items.map((n) => (
                  <li key={n.id} className="px-4 py-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium text-slate-800">{n.title}</p>
                      {!n.is_read && <Badge tone="indigo">New</Badge>}
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.message}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      <div className="mt-5 hidden">
        <StatusBadge status="ACTIVE" />
      </div>
    </div>
  );
}
