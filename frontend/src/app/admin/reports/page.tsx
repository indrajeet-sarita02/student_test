"use client";

import { useState } from "react";

import { reportsApi } from "@/lib/api/endpoints";
import type {
  ExamReportRow,
  QuestionReportRow,
  StudentReportRow,
  SubjectReportRow,
  TestReportRow,
} from "@/lib/types";
import { useApi } from "@/lib/hooks";
import { formatPercent } from "@/lib/utils";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Alert,
  Badge,
  Button,
  Card,
  CardBody,
  Input,
  PageHeader,
  Select,
  StatusBadge,
  Tabs,
} from "@/components/ui";
import { loadExamOptions, loadSubjectOptions } from "@/lib/options";

const TABS = [
  { id: "exams", label: "Exams" },
  { id: "tests", label: "Tests" },
  { id: "questions", label: "Questions" },
  { id: "subjects", label: "Subjects" },
  { id: "student", label: "Student" },
];

export default function AdminReportsPage() {
  const [tab, setTab] = useState("exams");

  return (
    <div>
      <PageHeader title="Reports" description="Performance and content analytics." />
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <div className="mt-4">
        {tab === "exams" && <ExamsReport />}
        {tab === "tests" && <TestsReport />}
        {tab === "questions" && <QuestionsReport />}
        {tab === "subjects" && <SubjectsReport />}
        {tab === "student" && <StudentReport />}
      </div>
    </div>
  );
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-slate-200 bg-white shadow-sm">{children}</div>;
}

function ExamsReport() {
  const report = useApi(() => reportsApi.exams());
  const columns: Column<ExamReportRow>[] = [
    {
      key: "exam_name",
      header: "Exam",
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.exam_name}</p>
          <p className="text-xs text-slate-400">{r.exam_code}</p>
        </div>
      ),
    },
    { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
    { key: "subject_count", header: "Subjects", align: "center", render: (r) => r.subject_count },
    { key: "question_count", header: "Questions", align: "center", render: (r) => r.question_count },
    { key: "test_count", header: "Tests", align: "center", render: (r) => r.test_count },
    { key: "attempt_count", header: "Attempts", align: "center", render: (r) => r.attempt_count },
    {
      key: "average_percentage",
      header: "Avg %",
      align: "right",
      render: (r) => formatPercent(r.average_percentage),
    },
  ];
  if (report.error) return <Alert tone="error">{report.error}</Alert>;
  return (
    <Wrapper>
      <DataTable
        columns={columns}
        rows={report.data ?? []}
        rowKey={(r) => r.exam_id}
        loading={report.loading}
        emptyTitle="No exam data"
      />
    </Wrapper>
  );
}

function TestsReport() {
  const [examId, setExamId] = useState("");
  const [examOptions, setExamOptions] = useState<Array<{ label: string; value: number }>>([]);
  useApi(() => loadExamOptions().then((o) => setExamOptions(o.map((x) => ({ label: x.label, value: Number(x.value) })))));
  const report = useApi(() => reportsApi.tests(examId ? Number(examId) : undefined), [examId]);

  const columns: Column<TestReportRow>[] = [
    {
      key: "test_name",
      header: "Test",
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.test_name}</p>
          <p className="text-xs text-slate-400">{r.test_code}</p>
        </div>
      ),
    },
    { key: "exam_name", header: "Exam", render: (r) => r.exam_name ?? "—" },
    { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
    { key: "attempt_count", header: "Attempts", align: "center", render: (r) => r.attempt_count },
    { key: "evaluated_count", header: "Evaluated", align: "center", render: (r) => r.evaluated_count },
    { key: "average_percentage", header: "Avg %", align: "right", render: (r) => formatPercent(r.average_percentage) },
    { key: "highest_percentage", header: "High %", align: "right", render: (r) => formatPercent(r.highest_percentage) },
    { key: "pass_rate", header: "Pass rate", align: "right", render: (r) => formatPercent(r.pass_rate) },
  ];

  return (
    <div>
      <div className="mb-3 w-full sm:w-56">
        <Select
          placeholder="All exams"
          options={examOptions}
          value={examId}
          onChange={(e) => setExamId(e.target.value)}
        />
      </div>
      {report.error ? (
        <Alert tone="error">{report.error}</Alert>
      ) : (
        <Wrapper>
          <DataTable
            columns={columns}
            rows={report.data ?? []}
            rowKey={(r) => r.test_id}
            loading={report.loading}
            emptyTitle="No test data"
          />
        </Wrapper>
      )}
    </div>
  );
}

function QuestionsReport() {
  const [subjectId, setSubjectId] = useState("");
  const [subjectOptions, setSubjectOptions] = useState<Array<{ label: string; value: number }>>([]);
  useApi(() =>
    loadSubjectOptions().then((o) => setSubjectOptions(o.map((x) => ({ label: x.label, value: Number(x.value) }))))
  );
  const report = useApi(
    () => reportsApi.questions(subjectId ? Number(subjectId) : undefined),
    [subjectId]
  );

  const columns: Column<QuestionReportRow>[] = [
    { key: "question_id", header: "ID", render: (r) => `#${r.question_id}` },
    { key: "subject_name", header: "Subject", render: (r) => r.subject_name ?? "—" },
    { key: "question_type", header: "Type", render: (r) => r.question_type.replace(/_/g, " ") },
    { key: "difficulty", header: "Difficulty", render: (r) => <Badge tone="amber">{r.difficulty}</Badge> },
    { key: "times_used", header: "Used", align: "center", render: (r) => r.times_used },
    { key: "times_answered", header: "Answered", align: "center", render: (r) => r.times_answered },
    { key: "correct_count", header: "Correct", align: "center", render: (r) => r.correct_count },
    { key: "accuracy", header: "Accuracy", align: "right", render: (r) => formatPercent(r.accuracy) },
  ];

  return (
    <div>
      <div className="mb-3 w-full sm:w-56">
        <Select
          placeholder="All subjects"
          options={subjectOptions}
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
        />
      </div>
      {report.error ? (
        <Alert tone="error">{report.error}</Alert>
      ) : (
        <Wrapper>
          <DataTable
            columns={columns}
            rows={report.data ?? []}
            rowKey={(r) => r.question_id}
            loading={report.loading}
            emptyTitle="No question data"
          />
        </Wrapper>
      )}
    </div>
  );
}

function SubjectsReport() {
  const [examId, setExamId] = useState("");
  const [examOptions, setExamOptions] = useState<Array<{ label: string; value: number }>>([]);
  useApi(() => loadExamOptions().then((o) => setExamOptions(o.map((x) => ({ label: x.label, value: Number(x.value) })))));
  const report = useApi(() => reportsApi.subjects(examId ? Number(examId) : undefined), [examId]);

  const columns: Column<SubjectReportRow>[] = [
    { key: "subject_name", header: "Subject", render: (r) => <span className="font-medium text-slate-900">{r.subject_name}</span> },
    { key: "exam_name", header: "Exam", render: (r) => r.exam_name ?? "—" },
    { key: "question_count", header: "Questions", align: "center", render: (r) => r.question_count },
    { key: "topic_count", header: "Topics", align: "center", render: (r) => r.topic_count },
    { key: "attempt_count", header: "Attempts", align: "center", render: (r) => r.attempt_count },
    { key: "average_percentage", header: "Avg %", align: "right", render: (r) => formatPercent(r.average_percentage) },
    { key: "accuracy", header: "Accuracy", align: "right", render: (r) => formatPercent(r.accuracy) },
  ];

  return (
    <div>
      <div className="mb-3 w-full sm:w-56">
        <Select
          placeholder="All exams"
          options={examOptions}
          value={examId}
          onChange={(e) => setExamId(e.target.value)}
        />
      </div>
      {report.error ? (
        <Alert tone="error">{report.error}</Alert>
      ) : (
        <Wrapper>
          <DataTable
            columns={columns}
            rows={report.data ?? []}
            rowKey={(r) => r.subject_id}
            loading={report.loading}
            emptyTitle="No subject data"
          />
        </Wrapper>
      )}
    </div>
  );
}

function StudentReport() {
  const [input, setInput] = useState("");
  const [studentId, setStudentId] = useState<number | null>(null);
  const report = useApi(
    () => (studentId ? reportsApi.student(studentId) : Promise.resolve(null)),
    [studentId]
  );

  const d = report.data as StudentReportRow | null;

  return (
    <div>
      <Card className="mb-4">
        <CardBody className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="w-full sm:max-w-xs">
            <Input
              label="Student ID"
              type="number"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. 12"
            />
          </div>
          <Button onClick={() => setStudentId(input ? Number(input) : null)}>Load report</Button>
        </CardBody>
      </Card>

      {report.error && <Alert tone="error">{report.error}</Alert>}
      {studentId && !report.loading && !d && !report.error && (
        <Alert tone="warning">No report found for student #{studentId}.</Alert>
      )}

      {d && (
        <Card>
          <CardBody>
            <div className="mb-4">
              <p className="text-lg font-semibold text-slate-900">{d.student_name}</p>
              <p className="text-sm text-slate-500">@{d.username} · ID #{d.student_id}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat label="Tests assigned" value={d.tests_assigned} />
              <Stat label="Attempts" value={d.attempts_taken} />
              <Stat label="Completed" value={d.tests_completed} />
              <Stat label="Rank" value={d.rank ?? "—"} />
              <Stat label="Average" value={formatPercent(d.average_percentage)} />
              <Stat label="Best" value={formatPercent(d.best_percentage)} />
              <Stat label="Avg score" value={d.average_score ?? "—"} />
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[10px] uppercase text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}
