"use client";

import Link from "next/link";
import { useState } from "react";

import { studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import type { AttemptResponse } from "@/lib/types";
import { formatDateTime, formatPercent } from "@/lib/utils";
import { Card, PageHeader, Pagination, StatusBadge } from "@/components/ui";
import { DataTable, type Column } from "@/components/DataTable";

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const attempts = useApi(
    () => studentApi.attempts({ page, page_size: pageSize }),
    [page]
  );

  const items = attempts.data?.items ?? [];

  const columns: Column<AttemptResponse>[] = [
    {
      key: "test",
      header: "Test",
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.test_name ?? `Test #${row.test_id}`}</p>
          <p className="text-xs text-slate-400">Attempt #{row.attempt_number}</p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "score",
      header: "Score",
      align: "right",
      render: (row) =>
        row.score === null ? (
          <span className="text-slate-400">—</span>
        ) : (
          <span className="font-medium">
            {row.score}/{row.max_score} ({formatPercent(row.percentage)})
          </span>
        ),
    },
    {
      key: "started",
      header: "Started",
      render: (row) => <span className="text-xs text-slate-500">{formatDateTime(row.started_at)}</span>,
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (row) => {
        const inProgress = row.status === "IN_PROGRESS" || row.status === "STARTED";
        return inProgress ? (
          <Link
            href={`/attempts/${row.id}`}
            className="text-xs font-medium text-amber-600 hover:underline"
          >
            Resume →
          </Link>
        ) : row.status === "SUBMITTED" || row.status === "EVALUATED" ? (
          <span className="text-xs text-slate-400">Completed</span>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        );
      },
      hideOnMobile: true,
    },
  ];

  return (
    <div>
      <PageHeader
        title="My Attempts"
        description="Every test attempt you have started, with status and scores."
      />

      <Card>
        {attempts.error ? (
          <div className="px-4 py-8 text-center text-sm text-rose-600">{attempts.error}</div>
        ) : (
          <DataTable
            columns={columns}
            rows={items}
            rowKey={(r) => r.id}
            loading={attempts.loading}
            emptyTitle="No attempts yet"
            emptyDescription="Once you start a test, your attempts will show up here."
          />
        )}
        {attempts.data && attempts.data.total > 0 && (
          <Pagination
            page={attempts.data.page}
            pageSize={attempts.data.page_size}
            total={attempts.data.total}
            totalPages={attempts.data.total_pages}
            onPageChange={setPage}
          />
        )}
      </Card>
    </div>
  );
}
