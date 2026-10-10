"use client";

import { examsApi } from "@/lib/api/endpoints";
import type { ExamResponse } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { CrudManager, type CrudField } from "@/components/admin/CrudManager";
import { Badge, StatusBadge } from "@/components/ui";
import { useToast } from "@/components/Toast";
import { isApiError } from "@/lib/api/client";

const EXAM_TYPES = ["NEET", "JEE", "UPSC", "SSC", "CUSTOM"];

const fields: CrudField[] = [
  { name: "name", label: "Name", type: "text", required: true, placeholder: "NEET 2026" },
  { name: "code", label: "Code", type: "text", required: true, placeholder: "NEET26" },
  {
    name: "exam_type",
    label: "Exam type",
    type: "select",
    options: EXAM_TYPES.map((t) => ({ label: t, value: t })),
    defaultValue: "CUSTOM",
  },
  { name: "duration_minutes", label: "Duration (minutes)", type: "number" },
  { name: "passing_percentage", label: "Passing %", type: "number" },
  { name: "start_at", label: "Start at", type: "datetime" },
  { name: "end_at", label: "End at", type: "datetime" },
  { name: "is_active", label: "Active", type: "checkbox", editOnly: true },
  { name: "description", label: "Description", type: "textarea", colSpan: 2 },
];

export default function AdminExamsPage() {
  const toast = useToast();

  return (
    <CrudManager<ExamResponse>
      title="Exams"
      description="Manage exams. Publish to make them available for tests."
      addLabel="New exam"
      api={{
        list: examsApi.list,
        create: examsApi.create,
        update: examsApi.update,
        remove: examsApi.remove,
      }}
      fields={fields}
      rowKey={(r) => r.id}
      filters={[
        { name: "exam_type", label: "Exam type", options: EXAM_TYPES.map((t) => ({ label: t, value: t })) },
        {
          name: "status",
          label: "Status",
          options: [
            { label: "Draft", value: "DRAFT" },
            { label: "Published", value: "PUBLISHED" },
            { label: "Archived", value: "ARCHIVED" },
          ],
        },
      ]}
      columns={[
        {
          key: "name",
          header: "Exam",
          render: (r) => (
            <div>
              <p className="font-medium text-slate-900">{r.name}</p>
              <p className="text-xs text-slate-400">{r.code}</p>
            </div>
          ),
        },
        { key: "exam_type", header: "Type", render: (r) => <Badge tone="indigo">{r.exam_type}</Badge> },
        { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
        {
          key: "duration_minutes",
          header: "Duration",
          render: (r) => (r.duration_minutes ? `${r.duration_minutes} min` : "—"),
        },
        {
          key: "start_at",
          header: "Starts",
          render: (r) => formatDate(r.start_at),
          hideOnMobile: true,
        },
        {
          key: "is_active",
          header: "Active",
          render: (r) => <Badge tone={r.is_active ? "green" : "slate"}>{r.is_active ? "Yes" : "No"}</Badge>,
        },
      ]}
      extraRowActions={(row, reload) => (
        <>
          {row.status === "DRAFT" && (
            <button
              type="button"
              className="text-xs font-medium text-emerald-600 hover:underline"
              onClick={async () => {
                try {
                  await examsApi.publish(row.id);
                  toast.success("Exam published.");
                  reload();
                } catch (err) {
                  toast.error(isApiError(err) ? err.message : "Unable to publish.");
                }
              }}
            >
              Publish
            </button>
          )}
          {row.status !== "ARCHIVED" && (
            <button
              type="button"
              className="text-xs font-medium text-slate-500 hover:underline"
              onClick={async () => {
                try {
                  await examsApi.archive(row.id);
                  toast.success("Exam archived.");
                  reload();
                } catch (err) {
                  toast.error(isApiError(err) ? err.message : "Unable to archive.");
                }
              }}
            >
              Archive
            </button>
          )}
        </>
      )}
    />
  );
}
