"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { questionsApi, testsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { QuestionResponse, TestQuestionResponse, TestResponse } from "@/lib/types";
import { downloadBlob, formatDateTime, toLocalInput } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { ConfirmDialog, Modal } from "@/components/Modal";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Input,
  Label,
  PageHeader,
  Pagination,
  SearchInput,
  Select,
  StatusBadge,
  Textarea,
} from "@/components/ui";
import { loadExamOptions } from "@/lib/options";
import { extractImportErrors, type ImportRowError } from "@/lib/test-import";

interface TestForm {
  exam_id: string;
  name: string;
  code: string;
  description: string;
  instructions: string;
  duration_minutes: string;
  total_marks: string;
  passing_marks: string;
  negative_marking_enabled: boolean;
  negative_marks: string;
  randomize_questions: boolean;
  randomize_options: boolean;
  max_attempts: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
}

const EMPTY: TestForm = {
  exam_id: "",
  name: "",
  code: "",
  description: "",
  instructions: "",
  duration_minutes: "180",
  total_marks: "0",
  passing_marks: "",
  negative_marking_enabled: true,
  negative_marks: "1",
  randomize_questions: false,
  randomize_options: false,
  max_attempts: "1",
  scheduled_start_at: "",
  scheduled_end_at: "",
};

export default function AdminTestsPage() {
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [examFilter, setExamFilter] = useState("");
  const [examOptions, setExamOptions] = useState<Array<{ label: string; value: number }>>([]);

  const [rows, setRows] = useState<TestResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = useCallback(() => setRefreshKey((k) => k + 1), []);

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<TestResponse | null>(null);
  const [form, setForm] = useState<TestForm>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<TestResponse | null>(null);
  const [deleting, setDeleting] = useState(false);

  // XLSX import
  const [importOpen, setImportOpen] = useState(false);
  const [importExamId, setImportExamId] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importRowErrors, setImportRowErrors] = useState<ImportRowError[]>([]);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);

  // Questions management
  const [qTarget, setQTarget] = useState<TestResponse | null>(null);
  const [attached, setAttached] = useState<TestQuestionResponse[]>([]);
  const [qLoading, setQLoading] = useState(false);
  const [bank, setBank] = useState<QuestionResponse[]>([]);
  const [bankLoading, setBankLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [savingQuestions, setSavingQuestions] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    loadExamOptions()
      .then((o) => setExamOptions(o.map((x) => ({ label: x.label, value: Number(x.value) }))))
      .catch(() => setExamOptions([]));
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await testsApi.list({
          page,
          page_size: 10,
          search: debounced || undefined,
          status: statusFilter || undefined,
          exam_id: examFilter || undefined,
        });
        if (!active) return;
        setRows(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load tests.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, debounced, statusFilter, examFilter, refreshKey]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY });
    setFormError(null);
    setOpen(true);
  };

  const openEdit = (t: TestResponse) => {
    setEditing(t);
    setForm({
      exam_id: String(t.exam_id),
      name: t.name,
      code: t.code,
      description: t.description ?? "",
      instructions: t.instructions ?? "",
      duration_minutes: String(t.duration_minutes),
      total_marks: String(t.total_marks),
      passing_marks: t.passing_marks === null ? "" : String(t.passing_marks),
      negative_marking_enabled: t.negative_marking_enabled,
      negative_marks: String(t.negative_marks),
      randomize_questions: t.randomize_questions,
      randomize_options: t.randomize_options,
      max_attempts: String(t.max_attempts),
      scheduled_start_at: toLocalInput(t.scheduled_start_at),
      scheduled_end_at: toLocalInput(t.scheduled_end_at),
    });
    setFormError(null);
    setOpen(true);
  };

  const setF = <K extends keyof TestForm>(k: K, v: TestForm[K]) => setForm((p) => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!form.name.trim()) return setFormError("Name is required.");
    if (!form.code.trim()) return setFormError("Code is required.");
    if (!form.exam_id) return setFormError("Exam is required.");

    const payload: Record<string, unknown> = {
      exam_id: Number(form.exam_id),
      name: form.name.trim(),
      code: form.code.trim(),
      description: form.description || null,
      instructions: form.instructions || null,
      duration_minutes: Number(form.duration_minutes) || 0,
      total_marks: Number(form.total_marks) || 0,
      passing_marks: form.passing_marks === "" ? null : Number(form.passing_marks),
      negative_marking_enabled: form.negative_marking_enabled,
      negative_marks: Number(form.negative_marks) || 0,
      randomize_questions: form.randomize_questions,
      randomize_options: form.randomize_options,
      max_attempts: Number(form.max_attempts) || 1,
      scheduled_start_at: form.scheduled_start_at ? new Date(form.scheduled_start_at).toISOString() : null,
      scheduled_end_at: form.scheduled_end_at ? new Date(form.scheduled_end_at).toISOString() : null,
    };

    setSaving(true);
    try {
      if (editing) await testsApi.update(editing.id, payload);
      else await testsApi.create(payload);
      toast.success(editing ? "Test updated." : "Test created.");
      setOpen(false);
      reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to save test.");
    } finally {
      setSaving(false);
    }
  };

  const publish = async (t: TestResponse) => {
    try {
      await testsApi.publish(t.id);
      toast.success("Test published.");
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to publish.");
    }
  };

  const close = async (t: TestResponse) => {
    try {
      await testsApi.close(t.id);
      toast.success("Test closed.");
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to close.");
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await testsApi.remove(deleteTarget.id);
      toast.success("Test deleted.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to delete.");
    } finally {
      setDeleting(false);
    }
  };

  const openImport = () => {
    setImportExamId("");
    setImportFile(null);
    setImportError(null);
    setImportRowErrors([]);
    setImportOpen(true);
  };

  const closeImport = () => {
    if (importing) return;
    setImportOpen(false);
  };

  const downloadTemplate = async () => {
    setDownloadingTemplate(true);
    try {
      const blob = await testsApi.importTemplate();
      downloadBlob(blob, "test_import_template.xlsx");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to download the template.");
    } finally {
      setDownloadingTemplate(false);
    }
  };

  const submitImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setImportError(null);
    setImportRowErrors([]);
    if (!importExamId) return setImportError("Select the exam the test belongs to.");
    if (!importFile) return setImportError("Choose an .xlsx file to import.");

    const form = new FormData();
    form.append("file", importFile);
    form.append("exam_id", importExamId);

    setImporting(true);
    try {
      const res = await testsApi.importXlsx(form);
      toast.success(
        `Imported "${res.name}" with ${res.questions_created} question(s).`
      );
      setImportOpen(false);
      reload();
    } catch (err) {
      if (isApiError(err)) {
        setImportError(err.message);
        setImportRowErrors(extractImportErrors(err.details));
      } else {
        setImportError("Unable to import the file.");
      }
    } finally {
      setImporting(false);
    }
  };

  const openQuestions = async (t: TestResponse) => {
    setQTarget(t);
    setSelectedIds([]);
    setQLoading(true);
    setBankLoading(true);
    try {
      const [attachedRes, bankRes] = await Promise.allSettled([
        testsApi.questions(t.id),
        questionsApi.list({ page_size: 100, status: "PUBLISHED", sort_by: "created_at", sort_order: "desc" }),
      ]);
      if (attachedRes.status === "fulfilled") setAttached(attachedRes.value);
      else setAttached([]);
      if (bankRes.status === "fulfilled") setBank(bankRes.value.items);
      else setBank([]);
    } finally {
      setQLoading(false);
      setBankLoading(false);
    }
  };

  const attachedQuestionIds = useMemo(() => new Set(attached.map((a) => a.question_id)), [attached]);

  const addSelected = async () => {
    if (!qTarget || selectedIds.length === 0) return;
    setSavingQuestions(true);
    try {
      await testsApi.bulkAddQuestions(qTarget.id, selectedIds, attached.length + 1);
      toast.success(`Added ${selectedIds.length} question(s).`);
      setSelectedIds([]);
      const res = await testsApi.questions(qTarget.id);
      setAttached(res);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to add questions.");
    } finally {
      setSavingQuestions(false);
    }
  };

  const removeAttached = async (questionId: number) => {
    if (!qTarget) return;
    try {
      await testsApi.removeQuestion(qTarget.id, questionId);
      setAttached((prev) => prev.filter((a) => a.question_id !== questionId));
      toast.success("Question removed.");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to remove question.");
    }
  };

  const columns: Column<TestResponse>[] = [
    {
      key: "name",
      header: "Test",
      render: (t) => (
        <div>
          <p className="font-medium text-slate-900">{t.name}</p>
          <p className="text-xs text-slate-400">{t.code}</p>
        </div>
      ),
    },
    { key: "status", header: "Status", render: (t) => <StatusBadge status={t.status} /> },
    {
      key: "question_count",
      header: "Questions",
      align: "center",
      render: (t) => <Badge tone="indigo">{t.question_count}</Badge>,
    },
    {
      key: "duration_minutes",
      header: "Duration",
      align: "center",
      render: (t) => `${t.duration_minutes} min`,
    },
    {
      key: "max_attempts",
      header: "Attempts",
      align: "center",
      render: (t) => t.max_attempts,
      hideOnMobile: true,
    },
    {
      key: "scheduled_start_at",
      header: "Scheduled",
      render: (t) => (
        <span className="text-xs text-slate-500">{t.scheduled_start_at ? formatDateTime(t.scheduled_start_at) : "—"}</span>
      ),
      hideOnMobile: true,
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (t) => (
        <div className="flex flex-wrap items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => openQuestions(t)}
            className="text-xs font-medium text-indigo-600 hover:underline"
          >
            Questions
          </button>
          {t.status === "DRAFT" && (
            <button
              type="button"
              onClick={() => publish(t)}
              className="text-xs font-medium text-emerald-600 hover:underline"
            >
              Publish
            </button>
          )}
          {t.status === "PUBLISHED" && (
            <button type="button" onClick={() => close(t)} className="text-xs font-medium text-amber-600 hover:underline">
              Close
            </button>
          )}
          <button type="button" onClick={() => openEdit(t)} className="text-xs font-medium text-brand-600 hover:underline">
            Edit
          </button>
          <button
            type="button"
            onClick={() => setDeleteTarget(t)}
            className="text-xs font-medium text-rose-600 hover:underline"
          >
            Delete
          </button>
        </div>
      ),
    },
  ];

  const availableQuestions = bank.filter((q) => !attachedQuestionIds.has(q.id));

  return (
    <div>
      <PageHeader
        title="Tests"
        description="Assemble questions into tests, then publish and assign them."
        actions={
          <>
            <Button variant="outline" onClick={openImport}>
              Import XLSX
            </Button>
            <Button onClick={openCreate}>+ New test</Button>
          </>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <SearchInput value={search} onChange={(v) => { setPage(1); setSearch(v); }} className="w-full sm:max-w-xs" />
        <div className="w-full sm:w-48">
          <Select
            placeholder="All exams"
            options={examOptions}
            value={examFilter}
            onChange={(e) => { setPage(1); setExamFilter(e.target.value); }}
          />
        </div>
        <div className="w-full sm:w-40">
          <Select
            placeholder="All statuses"
            options={[
              { label: "Draft", value: "DRAFT" },
              { label: "Published", value: "PUBLISHED" },
              { label: "Closed", value: "CLOSED" },
            ]}
            value={statusFilter}
            onChange={(e) => { setPage(1); setStatusFilter(e.target.value); }}
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
            rowKey={(t) => t.id}
            loading={loading}
            emptyTitle="No tests"
            emptyDescription="Create a test to get started."
          />
        )}
        {total > 0 && (
          <Pagination page={page} pageSize={10} total={total} totalPages={totalPages} onPageChange={setPage} />
        )}
      </div>

      {/* Create / edit */}
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? `Edit test #${editing.id}` : "New test"}
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="test-form" loading={saving}>
              {editing ? "Save changes" : "Create test"}
            </Button>
          </>
        }
      >
        <form id="test-form" onSubmit={submit} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Exam"
              required
              options={examOptions}
              placeholder="Select exam"
              value={form.exam_id}
              onChange={(e) => setF("exam_id", e.target.value)}
            />
            <Input label="Name" required value={form.name} onChange={(e) => setF("name", e.target.value)} />
            <Input label="Code" required value={form.code} onChange={(e) => setF("code", e.target.value)} />
            <Input
              label="Duration (minutes)"
              type="number"
              value={form.duration_minutes}
              onChange={(e) => setF("duration_minutes", e.target.value)}
            />
            <Input
              label="Total marks"
              type="number"
              value={form.total_marks}
              onChange={(e) => setF("total_marks", e.target.value)}
            />
            <Input
              label="Passing marks"
              type="number"
              value={form.passing_marks}
              onChange={(e) => setF("passing_marks", e.target.value)}
            />
            <Input
              label="Negative marks"
              type="number"
              value={form.negative_marks}
              onChange={(e) => setF("negative_marks", e.target.value)}
            />
            <Input
              label="Max attempts"
              type="number"
              value={form.max_attempts}
              onChange={(e) => setF("max_attempts", e.target.value)}
            />
            <Input
              label="Scheduled start"
              type="datetime-local"
              value={form.scheduled_start_at}
              onChange={(e) => setF("scheduled_start_at", e.target.value)}
            />
            <Input
              label="Scheduled end"
              type="datetime-local"
              value={form.scheduled_end_at}
              onChange={(e) => setF("scheduled_end_at", e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Checkbox
              label="Negative marking"
              checked={form.negative_marking_enabled}
              onChange={(e) => setF("negative_marking_enabled", e.target.checked)}
            />
            <Checkbox
              label="Randomize questions"
              checked={form.randomize_questions}
              onChange={(e) => setF("randomize_questions", e.target.checked)}
            />
            <Checkbox
              label="Randomize options"
              checked={form.randomize_options}
              onChange={(e) => setF("randomize_options", e.target.checked)}
            />
          </div>
          <Textarea label="Description" value={form.description} onChange={(e) => setF("description", e.target.value)} />
          <Textarea
            label="Instructions"
            value={form.instructions}
            onChange={(e) => setF("instructions", e.target.value)}
          />
        </form>
      </Modal>

      {/* Import from XLSX */}
      <Modal
        open={importOpen}
        onClose={closeImport}
        title="Import test from XLSX"
        description="Upload a workbook to create a new draft test with its questions."
        footer={
          <>
            <Button variant="outline" onClick={closeImport} disabled={importing}>
              Cancel
            </Button>
            <Button type="submit" form="test-import-form" loading={importing}>
              Import test
            </Button>
          </>
        }
      >
        <form id="test-import-form" onSubmit={submitImport} className="space-y-4">
          {importError && <Alert tone="error">{importError}</Alert>}

          <Select
            label="Exam"
            required
            options={examOptions}
            placeholder="Select exam"
            value={importExamId}
            onChange={(e) => setImportExamId(e.target.value)}
          />

          <div>
            <Label htmlFor="test-import-file" required>
              XLSX file
            </Label>
            <input
              id="test-import-file"
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm file:mr-3 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100"
            />
            <p className="mt-1 text-xs text-slate-500">
              One question per row on the “Questions” sheet; test settings on the “Test” sheet.
              Imported questions are created as drafts.
            </p>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
            <span className="text-xs text-slate-600">Need the column layout?</span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={downloadTemplate}
              loading={downloadingTemplate}
            >
              Download template
            </Button>
          </div>

          {importRowErrors.length > 0 && (
            <div className="max-h-56 overflow-y-auto rounded-lg border border-rose-200 bg-rose-50 p-3">
              <p className="mb-2 text-xs font-semibold text-rose-700">
                {importRowErrors.length} problem(s) found — fix these and upload again:
              </p>
              <ul className="space-y-1">
                {importRowErrors.map((err, index) => (
                  <li key={index} className="text-xs text-rose-700">
                    {err.row !== null ? `Row ${err.row}` : "File"}
                    {err.field ? ` · ${err.field}` : ""}: {err.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </form>
      </Modal>

      {/* Questions management */}
      <Modal
        open={Boolean(qTarget)}
        onClose={() => setQTarget(null)}
        title={`Questions — ${qTarget?.name ?? ""}`}
        size="xl"
        footer={
          <Button variant="outline" onClick={() => setQTarget(null)}>
            Done
          </Button>
        }
      >
        <div className="space-y-5">
          <div>
            <p className="mb-2 text-sm font-semibold text-slate-800">
              Attached questions ({attached.length})
            </p>
            {qLoading ? (
              <p className="text-sm text-slate-500">Loading…</p>
            ) : attached.length === 0 ? (
              <p className="text-sm text-slate-500">No questions attached yet.</p>
            ) : (
              <ul className="max-h-60 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200">
                {attached
                  .slice()
                  .sort((a, b) => a.question_order - b.question_order)
                  .map((a) => (
                    <li key={a.id} className="flex items-center justify-between gap-3 px-3 py-2">
                      <div className="min-w-0">
                        <p className="line-clamp-1 text-sm text-slate-800">
                          {a.question_order}. {a.question_text ?? `Question #${a.question_id}`}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          #{a.question_id} · {a.question_type?.replace(/_/g, " ") ?? ""}
                          {a.marks_override !== null ? ` · override ${a.marks_override}` : ""}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeAttached(a.question_id)}
                        className="shrink-0 text-xs font-medium text-rose-600 hover:underline"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
              </ul>
            )}
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-800">
                Add from bank ({availableQuestions.length} published)
              </p>
              <Button size="sm" onClick={addSelected} loading={savingQuestions} disabled={selectedIds.length === 0}>
                Add {selectedIds.length > 0 ? `(${selectedIds.length})` : ""}
              </Button>
            </div>
            {bankLoading ? (
              <p className="text-sm text-slate-500">Loading…</p>
            ) : availableQuestions.length === 0 ? (
              <p className="text-sm text-slate-500">
                No published questions available. Publish questions first.
              </p>
            ) : (
              <div className="max-h-64 overflow-y-auto rounded-lg border border-slate-200 p-3">
                <div className="space-y-2">
                  {availableQuestions.map((q) => (
                    <label key={q.id} className="flex cursor-pointer items-start gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600"
                        checked={selectedIds.includes(q.id)}
                        onChange={() =>
                          setSelectedIds((prev) =>
                            prev.includes(q.id) ? prev.filter((x) => x !== q.id) : [...prev, q.id]
                          )
                        }
                      />
                      <span className="text-slate-700">
                        <span className="line-clamp-2">{q.question_text}</span>
                        <span className="ml-1 text-[11px] text-slate-400">#{q.id}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete test?"
        message={`"${deleteTarget?.name ?? ""}" and its question links will be removed. This cannot be undone.`}
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
