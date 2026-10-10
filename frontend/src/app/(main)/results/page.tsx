"use client";

import Link from "next/link";
import { useState } from "react";

import { studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import type { ResultResponse } from "@/lib/types";
import { formatDateTime, formatPercent } from "@/lib/utils";
import { Badge, Card, PageHeader, Pagination, StatusBadge } from "@/components/ui";
import { DataTable, type Column } from "@/components/DataTable";

export default function ResultsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const results = useApi(
    () => studentApi.results({ page, page_size: pageSize }),
    [page]
  );

  const items = results.data?.items ?? [];

  const columns: Column<ResultResponse>[] = [
    {
      key: "test",
      header: "Test",
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">
            {row.test_name ?? `Test #${row.test_id}`}
          </p>
          <p className="text-xs text-slate-400">
            {row.attempt_number ? `Attempt #${row.attempt_number}` : ""}
          </p>
        </div>
      ),
    },
    {
      key: "score",
      header: "Score",
      render: (row) => (
        <span className="font-medium">
          {row.score}/{row.max_score}
        </span>
      ),
    },
    {
      key: "percentage",
      header: "Percentage",
      align: "right",
      render: (row) => (
        <span className="font-semibold">{formatPercent(row.percentage)}</span>
      ),
    },
    {
      key: "breakdown",
      header: "Correct / Wrong / Skipped",
      render: (row) => (
        <span className="text-xs text-slate-500">
          {row.correct_count} / {row.incorrect_count} / {row.unanswered_count}
        </span>
      ),
      hideOnMobile: true,
    },
    {
      key: "pass",
      header: "Result",
      render: (row) => (
        <Badge tone={row.pass_status ? "green" : "red"}>
          {row.pass_status ? "Pass" : "Fail"}
        </Badge>
      ),
    },
    {
      key: "published",
      header: "Published",
      render: (row) =>
        row.published_at ? (
          <StatusBadge status="PUBLISHED" />
        ) : (
          <Badge tone="amber">Pending</Badge>
        ),
      hideOnMobile: true,
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (row) => (
        <Link
          href={`/results/${row.id}`}
          className="text-xs font-medium text-brand-600 hover:underline"
        >
          Review →
        </Link>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="My Results"
        description="Scores and detailed review for your completed tests."
      />

      <Card>
        {results.error ? (
          <div className="px-4 py-8 text-center text-sm text-rose-600">{results.error}</div>
        ) : (
          <DataTable
            columns={columns}
            rows={items}
            rowKey={(r) => r.id}
            loading={results.loading}
            emptyTitle="No results yet"
            emptyDescription="Your results will appear here after you submit a test."
          />
        )}
        {results.data && results.data.total > 0 && (
          <Pagination
            page={results.data.page}
            pageSize={results.data.page_size}
            total={results.data.total}
            totalPages={results.data.total_pages}
            onPageChange={setPage}
          />
        )}
      </Card>

      {items.length > 0 && (
        <p className="mt-3 text-xs text-slate-400">
          Last updated {formatDateTime(items[0]?.created_at)}
        </p>
      )}
    </div>
  );
}
