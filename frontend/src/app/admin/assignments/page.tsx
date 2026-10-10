"use client";

import { useCallback, useEffect, useState } from "react";

import { assignmentsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { AssignmentResponse } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { ConfirmDialog, Modal } from "@/components/Modal";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Input,
  PageHeader,
  Pagination,
  SearchInput,
  Select,
  StatusBadge,
} from "@/components/ui";
import { loadStudentOptions, loadTestOptions } from "@/lib/options";

export default function AdminAssignmentsPage() {
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [testFilter, setTestFilter] = useState("");
  const [testOptions, setTestOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [studentOptions, setStudentOptions] = useState<Array<{ label: string; value: number }>>([]);

  const [rows, setRows] = useState<AssignmentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = useCallback(() => setRefreshKey((k) => k + 1), []);

  const [createOpen, setCreateOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [form, setForm] = useState({
    test_id: "",
    student_id: "",
    available_from: "",
    available_until: "",
    max_attempts: "",
  });
  const [bulk, setBulk] = useState({
    test_id: "",
    student_ids: [] as number[],
    available_from: "",
    available_until: "",
    max_attempts: "",
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AssignmentResponse | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

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
        const res = await assignmentsApi.list({
          page,
          page_size: 12,
          search: debounced || undefined,
          test_id: testFilter || undefined,
        });
        if (!active) return;
        setRows(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load assignments.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, debounced, testFilter, refreshKey]);

  const openCreate = () => {
    setForm({ test_id: "", student_id: "", available_from: "", available_until: "", max_attempts: "" });
    setFormError(null);
    setCreateOpen(true);
  };

  const openBulk = () => {
    setBulk({ test_id: "", student_ids: [], available_from: "", available_until: "", max_attempts: "" });
    setFormError(null);
    setBulkOpen(true);
  };

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!form.test_id || !form.student_id) return setFormError("Test and student are required.");
    setSaving(true);
    try {
      await assignmentsApi.create({
        test_id: Number(form.test_id),
        student_id: Number(form.student_id),
        available_from: form.available_from ? new Date(form.available_from).toISOString() : null,
        available_until: form.available_until ? new Date(form.available_until).toISOString() : null,
        max_attempts: form.max_attempts ? Number(form.max_attempts) : null,
      });
      toast.success("Assignment created.");
      setCreateOpen(false);
      reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to create assignment.");
    } finally {
      setSaving(false);
    }
  };

  const submitBulk = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!bulk.test_id) return setFormError("Select a test.");
    if (bulk.student_ids.length === 0) return setFormError("Select at least one student.");
    setSaving(true);
    try {
      const res = await assignmentsApi.bulk({
        test_id: Number(bulk.test_id),
        student_ids: bulk.student_ids,
        available_from: bulk.available_from ? new Date(bulk.available_from).toISOString() : null,
        available_until: bulk.available_until ? new Date(bulk.available_until).toISOString() : null,
        max_attempts: bulk.max_attempts ? Number(bulk.max_attempts) : null,
      });
      toast.success(`Created ${res.created}, skipped ${res.skipped}.`);
      setBulkOpen(false);
      reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to create assignments.");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await assignmentsApi.remove(deleteTarget.id);
      toast.success("Assignment removed.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to remove assignment.");
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<AssignmentResponse>[] = [
    {
      key: "test_name",
      header: "Test",
      render: (a) => <span className="font-medium text-slate-900">{a.test_name ?? `#${a.test_id}`}</span>,
    },
    {
      key: "student_name",
      header: "Student",
      render: (a) => (
        <div>
          <p className="text-slate-800">{a.student_name ?? `#${a.student_id}`}</p>
          {a.student_email && <p className="text-xs text-slate-400">{a.student_email}</p>}
        </div>
      ),
    },
    { key: "status", header: "Status", render: (a) => <StatusBadge status={a.status} /> },
    {
      key: "available_from",
      header: "Window",
      render: (a) => (
        <span className="text-xs text-slate-500">
          {a.available_from ? formatDateTime(a.available_from) : "any"} →{" "}
          {a.available_until ? formatDateTime(a.available_until) : "any"}
        </span>
      ),
      hideOnMobile: true,
    },
    {
      key: "max_attempts",
      header: "Attempts",
      align: "center",
      render: (a) => a.max_attempts ?? <Badge tone="slate">test default</Badge>,
      hideOnMobile: true,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Assignments"
        description="Assign tests to students and manage attempt windows."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={openBulk}>
              Bulk assign
            </Button>
            <Button onClick={openCreate}>+ Assign</Button>
          </div>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <SearchInput value={search} onChange={(v) => { setPage(1); setSearch(v); }} className="w-full sm:max-w-xs" />
        <div className="w-full sm:w-56">
          <Select
            placeholder="All tests"
            options={testOptions}
            value={testFilter}
            onChange={(e) => { setPage(1); setTestFilter(e.target.value); }}
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
            emptyTitle="No assignments"
            emptyDescription="Assign a test to a student to get started."
          />
        )}
        {total > 0 && (
          <Pagination page={page} pageSize={12} total={total} totalPages={totalPages} onPageChange={setPage} />
        )}
      </div>

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Assign test"
        footer={
          <>
            <Button variant="outline" onClick={() => setCreateOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="assign-form" loading={saving}>
              Assign
            </Button>
          </>
        }
      >
        <form id="assign-form" onSubmit={submitCreate} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}
          <Select
            label="Test"
            required
            options={testOptions}
            placeholder="Select test"
            value={form.test_id}
            onChange={(e) => setForm((p) => ({ ...p, test_id: e.target.value }))}
          />
          <Select
            label="Student"
            required
            options={studentOptions}
            placeholder="Select student"
            value={form.student_id}
            onChange={(e) => setForm((p) => ({ ...p, student_id: e.target.value }))}
          />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Available from"
              type="datetime-local"
              value={form.available_from}
              onChange={(e) => setForm((p) => ({ ...p, available_from: e.target.value }))}
            />
            <Input
              label="Available until"
              type="datetime-local"
              value={form.available_until}
              onChange={(e) => setForm((p) => ({ ...p, available_until: e.target.value }))}
            />
          </div>
          <Input
            label="Max attempts"
            type="number"
            help="Leave blank to use the test default."
            value={form.max_attempts}
            onChange={(e) => setForm((p) => ({ ...p, max_attempts: e.target.value }))}
          />
        </form>
      </Modal>

      <Modal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        title="Bulk assign test"
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setBulkOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="bulk-assign-form" loading={saving}>
              Assign {bulk.student_ids.length || ""}
            </Button>
          </>
        }
      >
        <form id="bulk-assign-form" onSubmit={submitBulk} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}
          <Select
            label="Test"
            required
            options={testOptions}
            placeholder="Select test"
            value={bulk.test_id}
            onChange={(e) => setBulk((p) => ({ ...p, test_id: e.target.value }))}
          />
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700">
                Students ({bulk.student_ids.length} selected)
              </span>
              <button
                type="button"
                className="text-xs font-medium text-brand-600 hover:underline"
                onClick={() =>
                  setBulk((p) => ({
                    ...p,
                    student_ids:
                      p.student_ids.length === studentOptions.length
                        ? []
                        : studentOptions.map((o) => o.value),
                  }))
                }
              >
                {bulk.student_ids.length === studentOptions.length ? "Clear all" : "Select all"}
              </button>
            </div>
            <div className="max-h-56 overflow-y-auto rounded-lg border border-slate-200 p-3">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {studentOptions.map((o) => (
                  <Checkbox
                    key={o.value}
                    label={o.label}
                    checked={bulk.student_ids.includes(o.value)}
                    onChange={(e) =>
                      setBulk((p) => ({
                        ...p,
                        student_ids: e.target.checked
                          ? [...p.student_ids, o.value]
                          : p.student_ids.filter((x) => x !== o.value),
                      }))
                    }
                  />
                ))}
                {studentOptions.length === 0 && (
                  <p className="text-xs text-slate-400">No students found.</p>
                )}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Available from"
              type="datetime-local"
              value={bulk.available_from}
              onChange={(e) => setBulk((p) => ({ ...p, available_from: e.target.value }))}
            />
            <Input
              label="Available until"
              type="datetime-local"
              value={bulk.available_until}
              onChange={(e) => setBulk((p) => ({ ...p, available_until: e.target.value }))}
            />
          </div>
          <Input
            label="Max attempts"
            type="number"
            help="Leave blank to use the test default."
            value={bulk.max_attempts}
            onChange={(e) => setBulk((p) => ({ ...p, max_attempts: e.target.value }))}
          />
        </form>
      </Modal>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Remove assignment?"
        message="The student will no longer be able to start this test."
        confirmLabel="Remove"
        loading={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
