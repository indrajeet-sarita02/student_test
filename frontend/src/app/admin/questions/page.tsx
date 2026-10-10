"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { questionsApi, subjectsApi, topicsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { OptionInput, QuestionResponse, TopicResponse } from "@/lib/types";
import { formatDate } from "@/lib/utils";
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
  Textarea,
} from "@/components/ui";

const QUESTION_TYPES = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE", "NUMERICAL", "SUBJECTIVE"];
const DIFFICULTIES = ["EASY", "MEDIUM", "HARD"];
const STATUSES = ["DRAFT", "PUBLISHED", "ARCHIVED"];
const CHOICE_TYPES = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"];

interface OptionRow {
  id?: number;
  option_text: string;
  is_correct: boolean;
}

interface FormState {
  subject_id: string;
  topic_id: string;
  question_type: string;
  question_text: string;
  explanation: string;
  difficulty: string;
  marks: string;
  negative_marks: string;
  status: string;
  source: string;
}

const EMPTY_FORM: FormState = {
  subject_id: "",
  topic_id: "",
  question_type: "SINGLE_CHOICE",
  question_text: "",
  explanation: "",
  difficulty: "MEDIUM",
  marks: "4",
  negative_marks: "0",
  status: "DRAFT",
  source: "",
};

export default function AdminQuestionsPage() {
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [filters, setFilters] = useState({ subject_id: "", question_type: "", difficulty: "", status: "" });

  const [data, setData] = useState<QuestionResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [subjectOptions, setSubjectOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [topicOptions, setTopicOptions] = useState<Array<{ label: string; value: number }>>([]);

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<QuestionResponse | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [options, setOptions] = useState<OptionRow[]>([
    { option_text: "", is_correct: true },
    { option_text: "", is_correct: false },
  ]);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<QuestionResponse | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Import
  const [importOpen, setImportOpen] = useState(false);
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);

  const reload = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    (async () => {
      try {
        const [subs, tops] = await Promise.allSettled([
          subjectsApi.list({ page_size: 100, sort_by: "name", sort_order: "asc" }),
          topicsApi.list({ page_size: 100, sort_by: "name", sort_order: "asc" }),
        ]);
        if (subs.status === "fulfilled")
          setSubjectOptions(subs.value.items.map((s) => ({ label: s.name, value: s.id })));
        if (tops.status === "fulfilled")
          setTopicOptions(tops.value.items.map((t: TopicResponse) => ({ label: t.name, value: t.id })));
      } catch {
        /* ignore */
      }
    })();
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await questionsApi.list({
          page,
          page_size: 10,
          search: debounced || undefined,
          subject_id: filters.subject_id || undefined,
          question_type: filters.question_type || undefined,
          difficulty: filters.difficulty || undefined,
          status: filters.status || undefined,
        });
        if (!active) return;
        setData(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load questions.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, debounced, filters, refreshKey]);

  const isChoice = CHOICE_TYPES.includes(form.question_type);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, subject_id: filters.subject_id || "" });
    setOptions([
      { option_text: "", is_correct: true },
      { option_text: "", is_correct: false },
    ]);
    setFormError(null);
    setOpen(true);
  };

  const openEdit = (q: QuestionResponse) => {
    setEditing(q);
    setForm({
      subject_id: String(q.subject_id),
      topic_id: q.topic_id ? String(q.topic_id) : "",
      question_type: q.question_type,
      question_text: q.question_text,
      explanation: q.explanation ?? "",
      difficulty: q.difficulty,
      marks: String(q.marks),
      negative_marks: String(q.negative_marks),
      status: q.status,
      source: q.source ?? "",
    });
    setOptions(
      q.options.length
        ? q.options
            .slice()
            .sort((a, b) => a.option_order - b.option_order)
            .map((o) => ({ id: o.id, option_text: o.option_text, is_correct: o.is_correct }))
        : [
            { option_text: "", is_correct: true },
            { option_text: "", is_correct: false },
          ]
    );
    setFormError(null);
    setOpen(true);
  };

  const setField = (key: keyof FormState, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const setCorrect = (index: number, checked: boolean) => {
    setOptions((prev) => {
      if (form.question_type === "MULTIPLE_CHOICE") {
        return prev.map((o, i) => (i === index ? { ...o, is_correct: checked } : o));
      }
      // single choice: one correct only
      return prev.map((o, i) => ({ ...o, is_correct: i === index ? checked : false }));
    });
  };

  const buildOptions = (): OptionInput[] =>
    options
      .filter((o) => o.option_text.trim() !== "")
      .map((o, i) => ({
        id: o.id,
        option_text: o.option_text.trim(),
        option_order: i + 1,
        is_correct: o.is_correct,
      }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!form.subject_id) return setFormError("Subject is required.");
    if (!form.question_text.trim()) return setFormError("Question text is required.");
    if (isChoice) {
      const filled = options.filter((o) => o.option_text.trim() !== "");
      if (filled.length < 2) return setFormError("Provide at least two options.");
      if (!options.some((o) => o.is_correct && o.option_text.trim() !== ""))
        return setFormError("Mark at least one correct option.");
      if (form.question_type !== "MULTIPLE_CHOICE" && options.filter((o) => o.is_correct).length !== 1)
        return setFormError("Exactly one option must be correct.");
    }

    const payload: Record<string, unknown> = {
      subject_id: Number(form.subject_id),
      topic_id: form.topic_id ? Number(form.topic_id) : null,
      question_type: form.question_type,
      question_text: form.question_text.trim(),
      explanation: form.explanation || null,
      difficulty: form.difficulty,
      marks: Number(form.marks) || 0,
      negative_marks: Number(form.negative_marks) || 0,
      status: form.status,
      source: form.source || null,
    };
    if (isChoice) payload.options = buildOptions();

    setSaving(true);
    try {
      if (editing) await questionsApi.update(editing.id, payload);
      else await questionsApi.create(payload);
      toast.success(editing ? "Question updated." : "Question created.");
      setOpen(false);
      reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to save question.");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await questionsApi.remove(deleteTarget.id);
      toast.success("Question deleted.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to delete question.");
    } finally {
      setDeleting(false);
    }
  };

  const publish = async (q: QuestionResponse) => {
    try {
      await questionsApi.publish(q.id);
      toast.success("Question published.");
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to publish.");
    }
  };

  const runImport = async () => {
    setImporting(true);
    try {
      const parsed = JSON.parse(importText);
      const questions = Array.isArray(parsed) ? parsed : parsed.questions;
      if (!Array.isArray(questions)) throw new Error("Expected a JSON array of questions.");
      const res = await questionsApi.import({ questions });
      toast.success(`Imported ${res.imported}, failed ${res.failed}.`);
      if (res.errors?.length) toast.error(res.errors.slice(0, 3).join("; "));
      setImportOpen(false);
      setImportText("");
      reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Import failed.");
    } finally {
      setImporting(false);
    }
  };

  const columns: Column<QuestionResponse>[] = useMemo(
    () => [
      {
        key: "question_text",
        header: "Question",
        render: (q) => (
          <div className="max-w-md">
            <p className="line-clamp-2 text-sm font-medium text-slate-900">{q.question_text}</p>
            <p className="mt-0.5 text-xs text-slate-400">
              #{q.id} · {q.marks} marks
            </p>
          </div>
        ),
      },
      {
        key: "question_type",
        header: "Type",
        render: (q) => <span className="text-xs text-slate-600">{q.question_type.replace(/_/g, " ")}</span>,
        hideOnMobile: true,
      },
      { key: "subject_id", header: "Subject", render: (q) => <span className="text-slate-500">#{q.subject_id}</span> },
      { key: "difficulty", header: "Difficulty", render: (q) => <Badge tone="amber">{q.difficulty}</Badge> },
      {
        key: "status",
        header: "Status",
        render: (q) => <StatusBadge status={q.status} />,
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (q) => (
          <div className="flex flex-wrap items-center justify-end gap-2">
            {q.status !== "PUBLISHED" && (
              <button
                type="button"
                onClick={() => publish(q)}
                className="text-xs font-medium text-emerald-600 hover:underline"
              >
                Publish
              </button>
            )}
            <button
              type="button"
              onClick={() => openEdit(q)}
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => setDeleteTarget(q)}
              className="text-xs font-medium text-rose-600 hover:underline"
            >
              Delete
            </button>
          </div>
        ),
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  return (
    <div>
      <PageHeader
        title="Questions"
        description="Author the question bank and publish questions for tests."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setImportOpen(true)}>
              Import
            </Button>
            <Button onClick={openCreate}>+ New question</Button>
          </div>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <SearchInput value={search} onChange={(v) => { setPage(1); setSearch(v); }} className="w-full sm:max-w-xs" />
        <div className="w-full sm:w-48">
          <Select
            placeholder="All subjects"
            options={subjectOptions}
            value={filters.subject_id}
            onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, subject_id: e.target.value })); }}
          />
        </div>
        <div className="w-full sm:w-44">
          <Select
            placeholder="All types"
            options={QUESTION_TYPES.map((t) => ({ label: t.replace(/_/g, " "), value: t }))}
            value={filters.question_type}
            onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, question_type: e.target.value })); }}
          />
        </div>
        <div className="w-full sm:w-36">
          <Select
            placeholder="Difficulty"
            options={DIFFICULTIES.map((d) => ({ label: d, value: d }))}
            value={filters.difficulty}
            onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, difficulty: e.target.value })); }}
          />
        </div>
        <div className="w-full sm:w-36">
          <Select
            placeholder="Status"
            options={STATUSES.map((s) => ({ label: s, value: s }))}
            value={filters.status}
            onChange={(e) => { setPage(1); setFilters((f) => ({ ...f, status: e.target.value })); }}
          />
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {error ? (
          <Alert tone="error" className="m-4">{error}</Alert>
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(q) => q.id}
            loading={loading}
            emptyTitle="No questions"
            emptyDescription="Create your first question to get started."
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
        title={editing ? `Edit question #${editing.id}` : "New question"}
        size="xl"
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="question-form" loading={saving}>
              {editing ? "Save changes" : "Create question"}
            </Button>
          </>
        }
      >
        <form id="question-form" onSubmit={submit} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Subject"
              required
              options={subjectOptions}
              placeholder="Select subject"
              value={form.subject_id}
              onChange={(e) => setField("subject_id", e.target.value)}
            />
            <Select
              label="Topic"
              options={topicOptions}
              placeholder="Optional"
              value={form.topic_id}
              onChange={(e) => setField("topic_id", e.target.value)}
            />
            <Select
              label="Type"
              options={QUESTION_TYPES.map((t) => ({ label: t.replace(/_/g, " "), value: t }))}
              value={form.question_type}
              onChange={(e) => setField("question_type", e.target.value)}
            />
            <Select
              label="Difficulty"
              options={DIFFICULTIES.map((d) => ({ label: d, value: d }))}
              value={form.difficulty}
              onChange={(e) => setField("difficulty", e.target.value)}
            />
            <Input label="Marks" type="number" value={form.marks} onChange={(e) => setField("marks", e.target.value)} />
            <Input
              label="Negative marks"
              type="number"
              value={form.negative_marks}
              onChange={(e) => setField("negative_marks", e.target.value)}
            />
            <Select
              label="Status"
              options={STATUSES.map((s) => ({ label: s, value: s }))}
              value={form.status}
              onChange={(e) => setField("status", e.target.value)}
            />
            <Input label="Source" value={form.source} onChange={(e) => setField("source", e.target.value)} />
          </div>

          <Textarea
            label="Question text"
            required
            value={form.question_text}
            onChange={(e) => setField("question_text", e.target.value)}
          />

          {isChoice && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-medium text-slate-700">Options</p>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setOptions((prev) => [...prev, { option_text: "", is_correct: false }])}
                >
                  + Add option
                </Button>
              </div>
              <div className="space-y-2">
                {options.map((o, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type={form.question_type === "MULTIPLE_CHOICE" ? "checkbox" : "radio"}
                      name="correct-option"
                      checked={o.is_correct}
                      onChange={(e) => setCorrect(i, e.target.checked)}
                      className="h-4 w-4 shrink-0 border-slate-300 text-brand-600"
                      title="Correct answer"
                    />
                    <Input
                      name={`option-${i}`}
                      placeholder={`Option ${i + 1}`}
                      value={o.option_text}
                      onChange={(e) =>
                        setOptions((prev) => prev.map((x, j) => (j === i ? { ...x, option_text: e.target.value } : x)))
                      }
                      className="flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => setOptions((prev) => prev.filter((_, j) => j !== i))}
                      className="shrink-0 rounded-lg border border-slate-200 px-2.5 py-2 text-sm text-slate-400 hover:bg-slate-50 hover:text-rose-600"
                      title="Remove option"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {form.question_type === "MULTIPLE_CHOICE"
                  ? "Tick all correct options."
                  : "Select the single correct option."}
              </p>
            </div>
          )}

          <Textarea
            label="Explanation"
            help="Shown to students during review."
            value={form.explanation}
            onChange={(e) => setField("explanation", e.target.value)}
          />
        </form>
      </Modal>

      {/* Import */}
      <Modal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        title="Import questions"
        description="Paste a JSON array of question objects."
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setImportOpen(false)} disabled={importing}>
              Cancel
            </Button>
            <Button onClick={runImport} loading={importing} disabled={!importText.trim()}>
              Import
            </Button>
          </>
        }
      >
        <textarea
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
          rows={14}
          placeholder={`[
  {
    "subject_id": 1,
    "question_type": "SINGLE_CHOICE",
    "question_text": "2 + 2 = ?",
    "difficulty": "EASY",
    "marks": 4,
    "negative_marks": 1,
    "options": [
      { "option_text": "3", "option_order": 1, "is_correct": false },
      { "option_text": "4", "option_order": 2, "is_correct": true }
    ]
  }
]`}
          className="w-full rounded-lg border border-slate-300 bg-slate-50 p-3 font-mono text-xs text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </Modal>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete question?"
        message="This action cannot be undone."
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
