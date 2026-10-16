"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { studentApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type {
  AnswerItem,
  StudentAttemptResponse,
  StudentQuestionView,
} from "@/lib/types";
import { cn, secondsToClock } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { Button, Spinner, StatusBadge } from "@/components/ui";
import { ConfirmDialog } from "@/components/Modal";

interface AnswerState extends AnswerItem {
  question_id: number;
}

export default function TestPlayerPage({ params }: { params: { attemptId: string } }) {
  const attemptId = Number(params.attemptId);
  const router = useRouter();
  const toast = useToast();

  const [attempt, setAttempt] = useState<StudentAttemptResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, AnswerState>>({});
  const [current, setCurrent] = useState(0);
  const [remaining, setRemaining] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirmSubmit, setConfirmSubmit] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const submittedRef = useRef(false);

  // ------------------------------------------------------------- initial load
  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const res = await studentApi.attempt(attemptId);
        if (!active) return;
        setAttempt(res);
        setRemaining(res.remaining_seconds ?? res.test.duration_minutes * 60);
        const map: Record<number, AnswerState> = {};
        for (const a of res.answers ?? []) {
          map[a.question_id] = {
            question_id: a.question_id,
            selected_option_id: a.selected_option_id,
            selected_option_ids: a.selected_option_ids,
            answer_text: a.answer_text,
            numerical_answer: a.numerical_answer,
            is_marked_for_review: a.is_marked_for_review,
          };
        }
        setAnswers(map);
      } catch (err) {
        if (active)
          setLoadError(isApiError(err) ? err.message : "Unable to load this attempt.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [attemptId]);

  // ------------------------------------------------------------- countdown
  useEffect(() => {
    if (remaining === null) return;
    if (remaining <= 0) return;
    const timer = setInterval(() => {
      setRemaining((prev) => (prev === null ? prev : Math.max(0, prev - 1)));
    }, 1000);
    return () => clearInterval(timer);
  }, [remaining === null, remaining === 0]); // eslint-disable-line react-hooks/exhaustive-deps

  const doSubmit = useCallback(
    async (auto = false) => {
      if (submittedRef.current) return;
      submittedRef.current = true;
      setSubmitting(true);
      try {
        const res = await studentApi.submit(attemptId);
        toast.success(
          auto ? "Time is up — your test was submitted automatically." : "Test submitted."
        );
        if (res.result_id) router.replace(`/results/${res.result_id}`);
        else router.replace("/history");
      } catch (err) {
        submittedRef.current = false;
        setSubmitting(false);
        toast.error(isApiError(err) ? err.message : "Unable to submit the test.");
      }
    },
    [attemptId, router, toast]
  );

  // Auto-submit when the clock reaches zero — but never for an attempt that is
  // already finished, otherwise the player fires a redundant submit that the
  // backend rejects with 409 and the user sees a spurious error toast.
  useEffect(() => {
    const status = attempt?.attempt.status;
    if (remaining === 0 && status === "IN_PROGRESS" && !submittedRef.current) {
      void doSubmit(true);
    }
  }, [remaining, attempt, doSubmit]);

  // Warn before leaving with unsaved work.
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (attempt && !submittedRef.current) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [attempt]);

  // ------------------------------------------------------------- persistence
  const persist = useCallback(
    async (map: Record<number, AnswerState>) => {
      setSaving(true);
      try {
        const payload: AnswerItem[] = Object.values(map).map((a) => ({
          question_id: a.question_id,
          selected_option_id: a.selected_option_id ?? null,
          selected_option_ids: a.selected_option_ids ?? null,
          answer_text: a.answer_text ?? null,
          numerical_answer: a.numerical_answer ?? null,
          is_marked_for_review: a.is_marked_for_review ?? false,
        }));
        const res = await studentApi.saveAnswers(attemptId, payload);
        setLastSaved(new Date());
        if (typeof res.remaining_count === "number") {
          // keep local state; server authoritative on submit
        }
      } catch (err) {
        toast.error(isApiError(err) ? err.message : "Could not save your answer.");
      } finally {
        setSaving(false);
      }
    },
    [attemptId, toast]
  );

  const scheduleSave = useCallback(
    (map: Record<number, AnswerState>) => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
      saveTimer.current = setTimeout(() => void persist(map), 900);
    },
    [persist]
  );

  const updateAnswer = useCallback(
    (questionId: number, patch: Partial<AnswerItem>) => {
      setAnswers((prev) => {
        const base: AnswerState = prev[questionId] ?? { question_id: questionId };
        const next = { ...prev, [questionId]: { ...base, ...patch, question_id: questionId } };
        scheduleSave(next);
        return next;
      });
    },
    [scheduleSave]
  );

  // Flush pending save before submit.
  const submitNow = async () => {
    setConfirmSubmit(false);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    try {
      await persist(answers);
    } catch {
      /* persist already toasts */
    }
    await doSubmit(false);
  };

  const questions = attempt?.questions ?? [];
  const question: StudentQuestionView | undefined = questions[current];

  const stats = useMemo(() => {
    const answered = questions.filter((q) => {
      const a = answers[q.id];
      if (!a) return false;
      if (q.question_type === "MULTIPLE_CHOICE")
        return (a.selected_option_ids?.length ?? 0) > 0;
      if (q.question_type === "NUMERICAL")
        return a.numerical_answer !== null && a.numerical_answer !== undefined && a.numerical_answer !== "";
      if (q.question_type === "SUBJECTIVE")
        return !!a.answer_text && a.answer_text.trim() !== "";
      return a.selected_option_id !== null && a.selected_option_id !== undefined;
    }).length;
    const marked = Object.values(answers).filter((a) => a.is_marked_for_review).length;
    return { answered, marked, total: questions.length };
  }, [answers, questions]);

  // ------------------------------------------------------------- rendering
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8 text-brand-600" />
      </div>
    );
  }

  if (loadError || !attempt) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <div className="text-4xl">⚠️</div>
        <p className="mt-3 text-sm text-slate-600">{loadError ?? "Attempt not found."}</p>
        <Link href="/history" className="mt-4 inline-block text-sm font-medium text-brand-600 hover:underline">
          ← My attempts
        </Link>
      </div>
    );
  }

  const finished = ["SUBMITTED", "EVALUATED", "EXPIRED"].includes(attempt.attempt.status);

  if (finished) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <div className="text-4xl">✅</div>
        <h1 className="mt-3 text-lg font-semibold text-slate-900">This attempt is already submitted</h1>
        <p className="mt-1 text-sm text-slate-500">You can review your results from the results page.</p>
        <div className="mt-5 flex justify-center gap-3">
          <Link
            href="/results"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            View results
          </Link>
          <Link
            href="/history"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            My attempts
          </Link>
        </div>
      </div>
    );
  }

  const palette = (
    <div className="space-y-4">
      <div className="grid grid-cols-6 gap-2 sm:grid-cols-5">
        {questions.map((q, idx) => {
          const a = answers[q.id];
          const isAnswered =
            a &&
            ((q.question_type === "MULTIPLE_CHOICE" && (a.selected_option_ids?.length ?? 0) > 0) ||
              (q.question_type === "NUMERICAL" && !!a.numerical_answer) ||
              (q.question_type === "SUBJECTIVE" && !!a.answer_text) ||
              (a.selected_option_id !== null && a.selected_option_id !== undefined &&
                !["MULTIPLE_CHOICE", "NUMERICAL", "SUBJECTIVE"].includes(q.question_type)));
          return (
            <button
              key={q.id}
              type="button"
              onClick={() => {
                setCurrent(idx);
                setPaletteOpen(false);
              }}
              className={cn(
                "relative flex h-9 w-9 items-center justify-center rounded-lg text-sm font-semibold transition-colors",
                idx === current && "ring-2 ring-brand-500 ring-offset-1",
                a?.is_marked_for_review
                  ? "bg-purple-500 text-white"
                  : isAnswered
                  ? "bg-emerald-500 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>
      <dl className="space-y-1 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-emerald-500" /> Answered ({stats.answered})
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-purple-500" /> Marked for review ({stats.marked})
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-slate-200" /> Not answered (
          {stats.total - stats.answered})
        </div>
      </dl>
    </div>
  );

  const remainingStr = secondsToClock(remaining);
  const lowTime = remaining !== null && remaining <= 60;

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Top bar */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-3 py-2.5 sm:px-5">
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold text-slate-900">
              {attempt.test.name}
            </h1>
            <p className="truncate text-xs text-slate-500">
              {stats.answered}/{stats.total} answered ·{" "}
              {saving ? "Saving…" : lastSaved ? `Saved ${lastSaved.toLocaleTimeString()}` : "Not saved yet"}
            </p>
          </div>
          <div
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm font-bold tabular-nums",
              lowTime ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-800"
            )}
          >
            ⏱ {remainingStr}
          </div>
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm text-slate-600 xl:hidden"
            onClick={() => setPaletteOpen((v) => !v)}
            aria-label="Question palette"
          >
            ☰
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-5 px-3 py-4 sm:px-5 xl:grid-cols-[1fr_260px]">
        {/* Question card */}
        <main>
          {question ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 sm:p-6">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="rounded-lg bg-brand-50 px-2 py-1 text-xs font-semibold text-brand-700">
                    Question {current + 1} of {questions.length}
                  </span>
                  <span className="text-xs text-slate-400">
                    +{question.marks} / -{question.negative_marks}
                  </span>
                  <StatusBadge status={question.difficulty} />
                </div>
                <button
                  type="button"
                  onClick={() =>
                    updateAnswer(question.id, {
                      is_marked_for_review: !answers[question.id]?.is_marked_for_review,
                    })
                  }
                  className={cn(
                    "whitespace-nowrap rounded-lg border px-2.5 py-1 text-xs font-medium",
                    answers[question.id]?.is_marked_for_review
                      ? "border-purple-300 bg-purple-50 text-purple-700"
                      : "border-slate-300 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {answers[question.id]?.is_marked_for_review ? "★ Marked" : "☆ Mark for review"}
                </button>
              </div>

              <p className="whitespace-pre-line text-sm font-medium text-slate-900 sm:text-base">
                {question.question_text}
              </p>

              <div className="mt-4 space-y-2">
                <QuestionInput
                  question={question}
                  answer={answers[question.id]}
                  onChange={(patch) => updateAnswer(question.id, patch)}
                />
              </div>

              <p className="mt-4 text-[11px] uppercase text-slate-400">
                {question.question_type.replace(/_/g, " ")}
              </p>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
              No questions in this test.
            </div>
          )}

          {/* Navigation */}
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrent((c) => Math.max(0, c - 1))}
                disabled={current === 0}
              >
                ← Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrent((c) => Math.min(questions.length - 1, c + 1))}
                disabled={current >= questions.length - 1}
              >
                Save &amp; Next →
              </Button>
            </div>
            <Button variant="success" size="sm" onClick={() => setConfirmSubmit(true)}>
              Submit test
            </Button>
          </div>
        </main>

        {/* Palette — desktop sidebar / mobile panel */}
        <aside className="hidden xl:block">
          <div className="sticky top-20 rounded-xl border border-slate-200 bg-white p-4">
            <p className="mb-3 text-xs font-semibold uppercase text-slate-400">Questions</p>
            {palette}
          </div>
        </aside>

        {paletteOpen && (
          <div className="fixed inset-0 z-40 xl:hidden">
            <div className="absolute inset-0 bg-slate-900/40" onClick={() => setPaletteOpen(false)} />
            <div className="absolute inset-x-0 bottom-0 max-h-[75vh] overflow-y-auto rounded-t-2xl bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-800">Questions</p>
                <button
                  type="button"
                  onClick={() => setPaletteOpen(false)}
                  className="rounded-md p-1 text-slate-400 hover:bg-slate-100"
                >
                  ✕
                </button>
              </div>
              {palette}
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmSubmit}
        title="Submit test?"
        message={`You have answered ${stats.answered} of ${stats.total} questions. Once submitted you cannot change your answers.`}
        confirmLabel="Submit"
        tone="primary"
        loading={submitting}
        onConfirm={submitNow}
        onClose={() => setConfirmSubmit(false)}
      />
    </div>
  );
}

function QuestionInput({
  question,
  answer,
  onChange,
}: {
  question: StudentQuestionView;
  answer?: AnswerState;
  onChange: (patch: Partial<AnswerItem>) => void;
}) {
  const type = question.question_type;

  if (type === "MULTIPLE_CHOICE") {
    const selected = answer?.selected_option_ids ?? [];
    return (
      <>
        {question.options.map((opt) => {
          const checked = selected.includes(opt.id);
          return (
            <label
              key={opt.id}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm transition-colors",
                checked ? "border-brand-400 bg-brand-50" : "border-slate-200 hover:bg-slate-50"
              )}
            >
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                checked={checked}
                onChange={() => {
                  const next = checked
                    ? selected.filter((x) => x !== opt.id)
                    : [...selected, opt.id];
                  onChange({ selected_option_ids: next });
                }}
              />
              <span className="text-slate-800">{opt.option_text}</span>
            </label>
          );
        })}
      </>
    );
  }

  if (type === "NUMERICAL") {
    return (
      <input
        type="number"
        step="any"
        inputMode="decimal"
        value={answer?.numerical_answer ?? ""}
        onChange={(e) => onChange({ numerical_answer: e.target.value })}
        placeholder="Enter your answer"
        className="w-full max-w-xs rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />
    );
  }

  if (type === "SUBJECTIVE") {
    return (
      <textarea
        value={answer?.answer_text ?? ""}
        onChange={(e) => onChange({ answer_text: e.target.value })}
        placeholder="Type your answer…"
        rows={5}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />
    );
  }

  // SINGLE_CHOICE and TRUE_FALSE
  return (
    <>
      {question.options.map((opt) => {
        const checked = answer?.selected_option_id === opt.id;
        return (
          <label
            key={opt.id}
            className={cn(
              "flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm transition-colors",
              checked ? "border-brand-400 bg-brand-50" : "border-slate-200 hover:bg-slate-50"
            )}
          >
            <input
              type="radio"
              name={`q-${question.id}`}
              className="h-4 w-4 border-slate-300 text-brand-600 focus:ring-brand-500"
              checked={checked}
              onChange={() => onChange({ selected_option_id: opt.id })}
            />
            <span className="text-slate-800">{opt.option_text}</span>
          </label>
        );
      })}
    </>
  );
}
