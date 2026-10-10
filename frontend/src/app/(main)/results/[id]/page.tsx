"use client";

import Link from "next/link";

import { studentApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { cn, formatPercent } from "@/lib/utils";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  LoadingBlock,
  PageHeader,
} from "@/components/ui";

export default function ResultReviewPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const review = useApi(() => studentApi.review(id), [id]);

  if (review.loading) return <LoadingBlock label="Loading result…" />;
  if (review.error || !review.data) {
    return (
      <EmptyState
        icon="🔍"
        title="Result not available"
        description={review.error ?? "This result could not be found or is not yet published."}
        action={
          <Link href="/results" className="text-sm font-medium text-brand-600 hover:underline">
            ← Back to results
          </Link>
        }
      />
    );
  }

  const { result, answers } = review.data;

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href="/results"
        className="mb-3 inline-block text-sm font-medium text-brand-600 hover:underline"
      >
        ← Back to results
      </Link>

      <PageHeader
        title={result.test_name ?? "Result"}
        description="Detailed answer review"
        actions={
          <Badge tone={result.pass_status ? "green" : "red"}>
            {result.pass_status ? "Passed" : "Failed"}
          </Badge>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Score</p>
          <p className="text-lg font-semibold text-slate-900">
            {result.score}/{result.max_score}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Percentage</p>
          <p className="text-lg font-semibold text-slate-900">
            {formatPercent(result.percentage)}
          </p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Rank</p>
          <p className="text-lg font-semibold text-slate-900">{result.rank ?? "—"}</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-[10px] uppercase text-slate-400">Percentile</p>
          <p className="text-lg font-semibold text-slate-900">
            {result.percentile === null ? "—" : formatPercent(result.percentile)}
          </p>
        </Card>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Badge tone="green">{result.correct_count} correct</Badge>
        <Badge tone="red">{result.incorrect_count} incorrect</Badge>
        <Badge tone="slate">{result.unanswered_count} skipped</Badge>
      </div>

      <h2 className="mb-3 mt-6 text-sm font-semibold text-slate-800">Answer review</h2>
      <div className="space-y-3">
        {answers.map((a, idx) => {
          const correct = a.is_correct === true;
          const wrong = a.is_correct === false;
          return (
            <Card key={`${a.question_id}-${idx}`}>
              <CardHeader
                title={`Q${idx + 1}. ${a.question_text}`}
                description={`${a.question_type} · ${a.marks_awarded}/${a.marks_possible} marks`}
                actions={
                  <Badge tone={correct ? "green" : wrong ? "red" : "slate"}>
                    {correct ? "Correct" : wrong ? "Incorrect" : "Skipped"}
                  </Badge>
                }
              />
              <CardBody className="space-y-2 text-sm">
                <p>
                  <span className="text-slate-400">Your answer:</span>{" "}
                  <span
                    className={cn(
                      "font-medium",
                      correct ? "text-emerald-700" : wrong ? "text-rose-700" : "text-slate-600"
                    )}
                  >
                    {a.your_answer || "—"}
                  </span>
                </p>
                {a.correct_answer && (
                  <p>
                    <span className="text-slate-400">Correct answer:</span>{" "}
                    <span className="font-medium text-emerald-700">{a.correct_answer}</span>
                  </p>
                )}
                {a.explanation && (
                  <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                    <span className="font-medium">Explanation: </span>
                    {a.explanation}
                  </p>
                )}
              </CardBody>
            </Card>
          );
        })}
        {answers.length === 0 && <EmptyState title="No answers to review" />}
      </div>
    </div>
  );
}
