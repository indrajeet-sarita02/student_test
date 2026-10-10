"use client";

import Link from "next/link";

import { studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import {
  Alert,
  Badge,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  LoadingBlock,
  PageHeader,
  StatusBadge,
} from "@/components/ui";
import { StartTestButton } from "@/components/student/StartTestButton";

export default function StudentTestDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = Number(params.id);
  const item = useApi(() => studentApi.test(id), [id]);

  if (item.loading) return <LoadingBlock label="Loading test…" />;
  if (item.error || !item.data) {
    return (
      <EmptyState
        icon="🔍"
        title="Test not available"
        description={item.error ?? "This test could not be found or is not assigned to you."}
        action={
          <Link href="/tests" className="text-sm font-medium text-brand-600 hover:underline">
            ← Back to tests
          </Link>
        }
      />
    );
  }

  const t = item.data;
  const inProgress =
    t.last_attempt_status === "IN_PROGRESS" || t.last_attempt_status === "STARTED";

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href="/tests"
        className="mb-3 inline-block text-sm font-medium text-brand-600 hover:underline"
      >
        ← Back to tests
      </Link>

      <PageHeader
        title={t.test.name}
        description={t.test.code}
        actions={<StatusBadge status={t.test.status} />}
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Duration</p>
          <p className="text-lg font-semibold text-slate-900">{t.test.duration_minutes} min</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Total marks</p>
          <p className="text-lg font-semibold text-slate-900">{t.test.total_marks}</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Passing</p>
          <p className="text-lg font-semibold text-slate-900">
            {t.test.passing_marks ?? "—"}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Attempts left</p>
          <p className="text-lg font-semibold text-slate-900">{t.attempts_remaining}</p>
        </Card>
      </div>

      {t.unavailable_reason && (
        <Alert tone="warning" className="mt-4">
          {t.unavailable_reason}
        </Alert>
      )}

      <Card className="mt-4">
        <CardHeader title="Instructions" />
        <CardBody>
          <p className="whitespace-pre-line text-sm text-slate-600">
            {t.test.instructions || "No instructions provided. Read each question carefully."}
          </p>
        </CardBody>
      </Card>

      {(t.available_from || t.available_until) && (
        <Card className="mt-4">
          <CardHeader title="Availability" />
          <CardBody className="space-y-1 text-sm text-slate-600">
            <p>
              <span className="text-slate-400">From:</span> {formatDateTime(t.available_from)}
            </p>
            <p>
              <span className="text-slate-400">Until:</span> {formatDateTime(t.available_until)}
            </p>
          </CardBody>
        </Card>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        {inProgress && t.last_attempt_id ? (
          <Link
            href={`/attempts/${t.last_attempt_id}`}
            className="inline-flex items-center justify-center rounded-lg bg-amber-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-600"
          >
            Resume attempt
          </Link>
        ) : t.can_attempt ? (
          <StartTestButton testId={t.test.id} label="Start test" size="md" />
        ) : (
          <Badge tone="slate">Not available to start</Badge>
        )}
        {t.best_percentage !== null && (
          <span className="text-sm text-slate-500">
            Best score: <strong>{t.best_percentage.toFixed(1)}%</strong>
          </span>
        )}
      </div>
    </div>
  );
}
