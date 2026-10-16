"use client";

import { useEffect, useState } from "react";

import { resultsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { ResultResponse } from "@/lib/types";
import { downloadBlob, formatDateTime, formatNumber, formatPercent } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { Modal } from "@/components/Modal";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Alert,
  Badge,
  Button,
  PageHeader,
  Pagination,
  Select,
} from "@/components/ui";
import { loadStudentOptions, loadTestOptions } from "@/lib/options";

export default function AdminResultsPage() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [testFilter, setTestFilter] = useState("");
  const [studentFilter, setStudentFilter] = useState("");
  const [publishedFilter, setPublishedFilter] = useState("");
  const [testOptions, setTestOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [studentOptions, setStudentOptions] = useState<Array<{ label: string; value: number }>>([]);

  const [rows, setRows] = useState<ResultResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [target, setTarget] = useState<ResultResponse | null>(null);

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
        const res = await resultsApi.list({
          page,
          page_size: 12,
          test_id: testFilter || undefined,
          student_id: studentFilter || undefined,
          published: publishedFilter === "" ? undefined : publishedFilter === "true",
        });
        if (!active) return;
        setRows(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load results.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, testFilter, studentFilter, publishedFilter]);

  const publish = async (r: ResultResponse) => {
    try {
      await resultsApi.publish(r.id);
      toast.success("Result published.");
      setRows((prev) => prev.map((x) => (x.id === r.id ? { ...x, published_at: new Date().toISOString() } : x)));
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to publish result.");
    }
  };

  const exportCsv = async () => {
    setExporting(true);
    try {
      const blob = await resultsApi.exportCsv({
        test_id: testFilter || undefined,
        student_id: studentFilter || undefined,
        published: publishedFilter === "" ? undefined : publishedFilter === "true",
      });
      downloadBlob(blob, "results.csv");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to export results.");
    } finally {
      setExporting(false);
    }
  };

  const columns: Column<ResultResponse>[] = [
    {
      key: "student_name",
      header: "Student",
      render: (r) => <span className="font-medium text-slate-900">{r.student_name ?? `#${r.student_id}`}</span>,
    },
    { key: "test_name", header: "Test", render: (r) => r.test_name ?? `#${r.test_id}` },
    {
      key: "score",
      header: "Score",
      align: "right",
      render: (r) => `${formatNumber(r.score, 1)} / ${formatNumber(r.max_score, 1)}`,
    },
    {
      key: "percentage",
      header: "%",
      align: "right",
      render: (r) => <span className="font-semibold">{formatPercent(r.percentage)}</span>,
    },
    {
      key: "breakdown",
      header: "C/I/U",
      align: "center",
      render: (r) => `${r.correct_count}/${r.incorrect_count}/${r.unanswered_count}`,
      hideOnMobile: true,
    },
    {
      key: "pass_status",
      header: "Pass",
      align: "center",
      render: (r) => <Badge tone={r.pass_status ? "green" : "red"}>{r.pass_status ? "Pass" : "Fail"}</Badge>,
    },
    {
      key: "published_at",
      header: "Published",
      render: (r) => (r.published_at ? <Badge tone="green">Yes</Badge> : <Badge tone="amber">No</Badge>),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) => (
        <div className="flex flex-wrap items-center justify-end gap-2">
          {!r.published_at && (
            <button
              type="button"
              onClick={() => publish(r)}
              className="text-xs font-medium text-emerald-600 hover:underline"
            >
              Publish
            </button>
          )}
          <button
            type="button"
            onClick={() => setTarget(r)}
            className="text-xs font-medium text-brand-600 hover:underline"
          >
            View
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Results"
        description="Publish results and export score data."
        actions={
          <Button variant="outline" onClick={exportCsv} loading={exporting}>
            Export CSV
          </Button>
        }
      />

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
            placeholder="Any publish state"
            options={[
              { label: "Published", value: "true" },
              { label: "Unpublished", value: "false" },
            ]}
            value={publishedFilter}
            onChange={(e) => {
              setPage(1);
              setPublishedFilter(e.target.value);
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
            rowKey={(r) => r.id}
            loading={loading}
            emptyTitle="No results"
          />
        )}
        {total > 0 && (
          <Pagination page={page} pageSize={12} total={total} totalPages={totalPages} onPageChange={setPage} />
        )}
      </div>

      <Modal open={Boolean(target)} onClose={() => setTarget(null)} title="Result detail" footer={
        <Button variant="outline" onClick={() => setTarget(null)}>Close</Button>
      }>
        {target && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Item label="Student" value={target.student_name ?? `#${target.student_id}`} />
              <Item label="Test" value={target.test_name ?? `#${target.test_id}`} />
              <Item label="Attempt" value={target.attempt_number ? `#${target.attempt_number}` : "—"} />
              <Item label="Score" value={`${formatNumber(target.score, 1)} / ${formatNumber(target.max_score, 1)}`} />
              <Item label="Percentage" value={formatPercent(target.percentage)} />
              <Item label="Pass" value={target.pass_status ? "Yes" : "No"} />
              <Item label="Correct" value={target.correct_count} />
              <Item label="Incorrect" value={target.incorrect_count} />
              <Item label="Unanswered" value={target.unanswered_count} />
              <Item label="Rank" value={target.rank ?? "—"} />
              <Item label="Percentile" value={formatPercent(target.percentile)} />
              <Item label="Published" value={target.published_at ? formatDateTime(target.published_at) : "No"} />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function Item({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[10px] uppercase text-slate-400">{label}</p>
      <p className="text-sm text-slate-800">{value}</p>
    </div>
  );
}
