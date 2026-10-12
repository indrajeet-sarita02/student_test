"use client";

import { useCallback, useEffect, useState } from "react";

import { attemptsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { AttemptDetailResponse, AttemptResponse } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { Modal } from "@/components/Modal";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Alert,
  Badge,
  Button,
  Card,
  Input,
  PageHeader,
  Pagination,
  Select,
  StatusBadge,
} from "@/components/ui";
import { loadStudentOptions, loadTestOptions } from "@/lib/options";

const STATUSES = ["IN_PROGRESS", "SUBMITTED", "EVALUATED", "EXPIRED", "CANCELLED"];

export default function AdminAttemptsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [testFilter, setTestFilter] = useState("");
  const [studentFilter, setStudentFilter] = useState("");
  const [testOptions, setTestOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [studentOptions, setStudentOptions] = useState<Array<{ label: string; value: number }>>([]);

  const [rows, setRows] = useState<AttemptResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [detail, setDetail] = useState<AttemptDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    loadTestOptions()
      .then((o) => setTestOptions(o.map((x) => ({ label: x.label, value: Number(x.value) }))))
      .catch(() => setTestOptions([]));
    loadStudentOptions()
      .then((o) => setStudentOptions(o.map((x) => ({ label: x.label, value: Number(x.value) }))))
      .catch(() => setStudentOptions([]));
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await attemptsApi.list({
          page,
          page_size: 12,
          status: statusFilter || undefined,
          test_id: testFilter || undefined,
          student_id: studentFilter || undefined,
        });
        if (!active) return;
        setRows(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load attempts.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, statusFilter, testFilter, studentFilter]);

  const openDetail = async (attempt: AttemptResponse) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetail(null);
    try {
      const res = await attemptsApi.get(attempt.id);
      setDetail(res);
    } catch (err) {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const columns: Column<AttemptResponse>[] = [
    {
      key: "student_name",
      header: "Student",
      render: (a) => <span className="font-medium text-slate-900">{a.student_name ?? `#${a.student_id}`}</span>,
    },
    { key: "test_name", header: "Test", render: (a) => a.test_name ?? `#${a.test_id}` },
    {
      key: "attempt_number",
      header: "Attempt",
      align: "center",
      render: (a) => <Badge tone="indigo">#{a.attempt_number}</Badge>,
    },
    { key: "status", header: "Status", render: (a) => <StatusBadge status={a.status} /> },
    {
      key: "score",
      header: "Score",
      align: "right",
      render: (a) =>
        a.score === null ? (
          <span className="text-slate-400">—</span>
        ) : (
          <span>
            {a.score}/{a.max_score}
            {a.percentage !== null && <span className="ml-1 text-xs text-slate-400">{a.percentage.toFixed(1)}%</span>}
          </span>
        ),
    },
    {
      key: "submitted_at",
      header: "Submitted",
      render: (a) => <span className="text-xs text-slate-500">{formatDateTime(a.submitted_at)}</span>,
      hideOnMobile: true,
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (a) => (
        <button
          type="button"
          onClick={() => openDetail(a)}
          className="text-xs font-medium text-brand-600 hover:underline"
        >
          View
        </button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="Attempts" description="Monitor student attempts, progress and scores." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="w-full sm:w-56">
          <Select
            placeholder="All tests"
            options={testOptions}
            value={testFilter}
            onChange={(e) => {
              setPage(1);
              setTestFilter(e.target.value);
            }}
          />
        </div>
        <div className="w-full sm:w-56">
          <Select
            placeholder="All students"
            options={studentOptions}
            value={studentFilter}
            onChange={(e) => {
              setPage(1);
              setStudentFilter(e.target.value);
            }}
          />
        </div>
        <div className="w-full sm:w-40">
          <Select
            placeholder="Status"
            options={STATUSES.map((s) => ({ label: s, value: s }))}
            value={statusFilter}
            onChange={(e) => {
              setPage(1);
              setStatusFilter(e.target.value);
            }}
          />
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {error ? (
          <Alert tone="error" className="m-4">{error}</Alert>
        ) : (
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(a) => a.id}
            loading={loading}
            emptyTitle="No attempts"
          />
        )}
        {total > 0 && (
          <Pagination page={page} pageSize={12} total={total} totalPages={totalPages} onPageChange={setPage} />
        )}
      </div>

      <Modal
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        title="Attempt detail"
        size="xl"
        footer={
          <Button variant="outline" onClick={() => setDetailOpen(false)}>
            Close
          </Button>
        }
      >
        {detailLoading ? (
          <p className="py-6 text-center text-sm text-slate-500">Loading…</p>
        ) : !detail ? (
          <p className="py-6 text-center text-sm text-slate-500">Could not load attempt.</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Info label="Student" value={detail.attempt.student_name ?? `#${detail.attempt.student_id}`} />
              <Info label="Test" value={detail.attempt.test_name ?? `#${detail.attempt.test_id}`} />
              <Info label="Status" value={<StatusBadge status={detail.attempt.status} />} />
              <Info label="Attempt" value={`#${detail.attempt.attempt_number}`} />
              <Info label="Started" value={formatDateTime(detail.attempt.started_at)} />
              <Info label="Submitted" value={formatDateTime(detail.attempt.submitted_at)} />
              <Info
                label="Score"
                value={detail.attempt.score === null ? "—" : `${detail.attempt.score}/${detail.attempt.max_score}`}
              />
              <Info
                label="Percentage"
                value={detail.attempt.percentage === null ? "—" : `${detail.attempt.percentage.toFixed(1)}%`}
              />
            </div>

            {detail.result && (
              <Card className="p-3">
                <p className="mb-2 text-xs font-semibold uppercase text-slate-400">Result</p>
                <div className="flex flex-wrap gap-2 text-sm">
                  <Badge tone="green">{detail.result.correct_count} correct</Badge>
                  <Badge tone="red">{detail.result.incorrect_count} incorrect</Badge>
                  <Badge tone="slate">{detail.result.unanswered_count} skipped</Badge>
                  <Badge tone={detail.result.pass_status ? "green" : "red"}>
                    {detail.result.pass_status ? "Pass" : "Fail"}
                  </Badge>
                  {detail.result.rank !== null && <Badge tone="indigo">Rank {detail.result.rank}</Badge>}
                </div>
              </Card>
            )}

            <div>
              <p className="mb-2 text-sm font-semibold text-slate-800">
                Answers ({detail.answers.length})
              </p>
              <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-50">
                    <tr className="text-left text-xs uppercase text-slate-500">
                      <th className="px-3 py-2">Question</th>
                      <th className="px-3 py-2">Answer</th>
                      <th className="px-3 py-2 text-center">Result</th>
                      <th className="px-3 py-2 text-right">Marks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {detail.answers.map((a) => (
                      <tr key={a.id}>
                        <td className="max-w-xs px-3 py-2 text-slate-700">
                          <span className="line-clamp-2">{a.question_text ?? `#${a.question_id}`}</span>
                        </td>
                        <td className="px-3 py-2 text-slate-600">
                          {a.answer_text ||
                            a.numerical_answer ||
                            a.selected_option_text ||
                            (a.selected_option_ids?.length
                              ? a.selected_option_ids.join(", ")
                              : a.selected_option_id !== null && a.selected_option_id !== undefined
                              ? `option ${a.selected_option_id}`
                              : "—")}
                        </td>
                        <td className="px-3 py-2 text-center">
                          {a.is_correct === null ? (
                            <Badge tone="slate">—</Badge>
                          ) : a.is_correct ? (
                            <Badge tone="green">Correct</Badge>
                          ) : (
                            <Badge tone="red">Wrong</Badge>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-600">
                          {a.marks_awarded ?? "—"}
                        </td>
                      </tr>
                    ))}
                    {detail.answers.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-3 py-6 text-center text-slate-400">
                          No answers recorded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function Info({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[10px] uppercase text-slate-400">{label}</p>
      <div className="text-sm text-slate-800">{value}</div>
    </div>
  );
}
