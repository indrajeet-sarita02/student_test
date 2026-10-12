"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { testsApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import type { TestImportResponse } from "@/lib/types";
import { downloadBlob, formatNumber } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import {
  Alert,
  Button,
  Card,
  CardBody,
  CardHeader,
  Label,
  PageHeader,
  Select,
  StatCard,
} from "@/components/ui";
import { loadExamOptions } from "@/lib/options";
import { extractImportErrors, formatImportError, type ImportRowError } from "@/lib/test-import";

export default function AdminUploadPage() {
  const toast = useToast();

  const [examOptions, setExamOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [examId, setExamId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rowErrors, setRowErrors] = useState<ImportRowError[]>([]);
  const [result, setResult] = useState<TestImportResponse | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);

  useEffect(() => {
    loadExamOptions()
      .then((o) => setExamOptions(o.map((x) => ({ label: x.label, value: Number(x.value) }))))
      .catch(() => setExamOptions([]));
  }, []);

  const downloadTemplate = async () => {
    setDownloading(true);
    try {
      const blob = await testsApi.importTemplate();
      downloadBlob(blob, "test_import_template.xlsx");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to download the template.");
    } finally {
      setDownloading(false);
    }
  };

  const reset = () => {
    setExamId("");
    setFile(null);
    setError(null);
    setRowErrors([]);
    setResult(null);
    setFileInputKey((k) => k + 1);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setRowErrors([]);
    setResult(null);
    if (!examId) return setError("Select the exam the test belongs to.");
    if (!file) return setError("Choose an .xlsx file to import.");

    const form = new FormData();
    form.append("file", file);
    form.append("exam_id", examId);

    setBusy(true);
    try {
      const res = await testsApi.importXlsx(form);
      setResult(res);
      toast.success(`Imported "${res.name}" with ${res.questions_created} question(s).`);
      setFile(null);
      setFileInputKey((k) => k + 1);
    } catch (err) {
      if (isApiError(err)) {
        setError(err.message);
        setRowErrors(extractImportErrors(err.details));
      } else {
        setError("Unable to import the file.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Upload XLSX"
        description="Import a test and its questions from an Excel workbook."
        actions={
          <Button variant="outline" onClick={downloadTemplate} loading={downloading}>
            Download template
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Import workbook"
            description="The workbook must contain a 'Test' sheet and a 'Questions' sheet."
          />
          <CardBody>
            <form onSubmit={submit} className="space-y-4">
              {error && <Alert tone="error">{error}</Alert>}

              <Select
                label="Exam"
                required
                options={examOptions}
                placeholder="Select exam"
                value={examId}
                onChange={(e) => setExamId(e.target.value)}
              />

              <div>
                <Label htmlFor="upload-xlsx-file" required>
                  XLSX file
                </Label>
                <input
                  key={fileInputKey}
                  id="upload-xlsx-file"
                  type="file"
                  accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm file:mr-3 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100"
                />
                <p className="mt-1 text-xs text-slate-500">
                  One question per row on the “Questions” sheet; test settings on the “Test” sheet.
                  Imported questions are created as drafts.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button type="submit" loading={busy}>
                  Import test
                </Button>
                <Button type="button" variant="outline" onClick={reset} disabled={busy}>
                  Clear
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="How it works" />
          <CardBody className="space-y-3 text-sm text-slate-600">
            <p>
              1. Download the template and fill the <strong>Test</strong> and{" "}
              <strong>Questions</strong> sheets.
            </p>
            <p>2. Pick the exam, choose the file and submit.</p>
            <p>
              Subjects and topics referenced by code/name are created automatically inside the
              chosen exam.
            </p>
            <p className="text-xs text-slate-500">
              The import is all-or-nothing: if any row is invalid nothing is created and every
              problem is listed on the left.
            </p>
          </CardBody>
        </Card>
      </div>

      {rowErrors.length > 0 && (
        <div className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4">
          <p className="mb-2 text-sm font-semibold text-rose-700">
            {rowErrors.length} problem(s) found — fix these and upload again:
          </p>
          <ul className="max-h-72 space-y-1 overflow-y-auto">
            {rowErrors.map((err, index) => (
              <li key={index} className="text-xs text-rose-700">
                {formatImportError(err)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result && (
        <div className="mt-5 space-y-4">
          <Alert tone="success">
            Created draft test <strong>{result.name}</strong> ({result.test_code}).
          </Alert>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Questions" value={result.questions_created} icon="❓" />
            <StatCard label="Subjects created" value={result.subjects_created} icon="📚" />
            <StatCard label="Topics created" value={result.topics_created} icon="🗂️" />
            <StatCard label="Total marks" value={formatNumber(result.total_marks, 0)} icon="🎯" />
          </div>
          <div>
            <Link
              href="/admin/tests"
              className="text-sm font-medium text-brand-600 hover:underline"
            >
              View imported tests →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
