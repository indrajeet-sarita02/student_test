"use client";

import { subjectsApi } from "@/lib/api/endpoints";
import type { SubjectResponse } from "@/lib/types";
import { loadExamOptions } from "@/lib/options";
import { CrudManager, type CrudField } from "@/components/admin/CrudManager";
import { Badge } from "@/components/ui";

const fields: CrudField[] = [
  {
    name: "exam_id",
    label: "Exam",
    type: "select",
    required: true,
    loadOptions: loadExamOptions,
  },
  { name: "name", label: "Name", type: "text", required: true, placeholder: "Physics" },
  { name: "code", label: "Code", type: "text", required: true, placeholder: "PHY" },
  { name: "sort_order", label: "Sort order", type: "number", defaultValue: "0" },
  { name: "is_active", label: "Active", type: "checkbox", editOnly: true, defaultValue: true },
  { name: "description", label: "Description", type: "textarea", colSpan: 2 },
];

export default function AdminSubjectsPage() {
  return (
    <CrudManager<SubjectResponse>
      title="Subjects"
      description="Subjects belong to an exam and group questions and topics."
      addLabel="New subject"
      api={{
        list: subjectsApi.list,
        create: subjectsApi.create,
        update: subjectsApi.update,
        remove: subjectsApi.remove,
      }}
      fields={fields}
      rowKey={(r) => r.id}
      filters={[{ name: "exam_id", label: "Exam", loadOptions: loadExamOptions }]}
      columns={[
        {
          key: "name",
          header: "Subject",
          render: (r) => (
            <div>
              <p className="font-medium text-slate-900">{r.name}</p>
              <p className="text-xs text-slate-400">{r.code}</p>
            </div>
          ),
        },
        { key: "exam_id", header: "Exam", render: (r) => <span className="text-slate-500">#{r.exam_id}</span> },
        { key: "sort_order", header: "Order", render: (r) => r.sort_order },
        {
          key: "is_active",
          header: "Active",
          render: (r) => <Badge tone={r.is_active ? "green" : "slate"}>{r.is_active ? "Yes" : "No"}</Badge>,
        },
      ]}
    />
  );
}
