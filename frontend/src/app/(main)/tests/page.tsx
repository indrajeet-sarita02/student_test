"use client";

import Link from "next/link";
import { useState } from "react";

import { studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import {
  Badge,
  Card,
  EmptyState,
  LoadingBlock,
  PageHeader,
  SearchInput,
  StatusBadge,
} from "@/components/ui";
import { StartTestButton } from "@/components/student/StartTestButton";

export default function StudentTestsPage() {
  const [search, setSearch] = useState("");
  const tests = useApi(() => studentApi.tests(search || undefined), [search]);

  const items = tests.data ?? [];

  return (
    <div>
      <PageHeader
        title="Available Tests"
        description="Tests assigned to you. Start a new attempt or resume one in progress."
      />

      <div className="mb-4 max-w-sm">
        <SearchInput value={search} onChange={setSearch} placeholder="Search tests…" />
      </div>

      {tests.loading ? (
        <LoadingBlock />
      ) : tests.error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-6 text-sm text-rose-700">
          {tests.error}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon="🧪"
            title="No tests assigned"
            description="You don't have any tests available right now. Check back later."
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => {
            const inProgress =
              item.last_attempt_status === "IN_PROGRESS" ||
              item.last_attempt_status === "STARTED";
            return (
              <Card key={item.assignment_id} className="flex flex-col p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-slate-900">
                      {item.test.name}
                    </h3>
                    <p className="mt-0.5 text-xs text-slate-500">{item.test.code}</p>
                  </div>
                  <StatusBadge status={item.test.status} />
                </div>

                {item.test.instructions && (
                  <p className="mt-2 line-clamp-2 text-xs text-slate-500">
                    {item.test.instructions}
                  </p>
                )}

                <dl className="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-slate-50 px-2 py-1.5">
                    <dt className="text-[10px] uppercase text-slate-400">Duration</dt>
                    <dd className="text-sm font-semibold text-slate-800">
                      {item.test.duration_minutes}m
                    </dd>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-2 py-1.5">
                    <dt className="text-[10px] uppercase text-slate-400">Marks</dt>
                    <dd className="text-sm font-semibold text-slate-800">
                      {item.test.total_marks}
                    </dd>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-2 py-1.5">
                    <dt className="text-[10px] uppercase text-slate-400">Attempts</dt>
                    <dd className="text-sm font-semibold text-slate-800">
                      {item.attempts_used}/{item.max_attempts ?? "∞"}
                    </dd>
                  </div>
                </dl>

                <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                  <Badge tone={item.attempts_remaining > 0 ? "green" : "slate"}>
                    {item.attempts_remaining > 0
                      ? `${item.attempts_remaining} attempt(s) left`
                      : "No attempts left"}
                  </Badge>
                  {item.best_percentage !== null && (
                    <Badge tone="indigo">Best {item.best_percentage.toFixed(0)}%</Badge>
                  )}
                </div>

                {(item.available_from || item.available_until) && (
                  <p className="mt-2 text-[11px] text-slate-400">
                    Window: {formatDateTime(item.available_from)} →{" "}
                    {formatDateTime(item.available_until)}
                  </p>
                )}

                {item.unavailable_reason && (
                  <p className="mt-2 text-[11px] text-amber-600">{item.unavailable_reason}</p>
                )}

                <div className="mt-4 flex items-center gap-2">
                  {inProgress && item.last_attempt_id ? (
                    <Link
                      href={`/attempts/${item.last_attempt_id}`}
                      className="inline-flex items-center justify-center rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
                    >
                      Resume attempt
                    </Link>
                  ) : item.can_attempt ? (
                    <StartTestButton testId={item.test.id} label="Start test" />
                  ) : (
                    <button
                      disabled
                      className="cursor-not-allowed rounded-lg bg-slate-200 px-4 py-2 text-sm font-medium text-slate-400"
                    >
                      Unavailable
                    </button>
                  )}
                  <Link
                    href={`/tests/${item.test.id}`}
                    className="text-xs font-medium text-brand-600 hover:underline"
                  >
                    Details
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
