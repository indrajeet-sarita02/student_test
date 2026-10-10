"use client";

import { topicsApi } from "@/lib/api/endpoints";
import type { TopicResponse } from "@/lib/types";
import { loadSubjectOptions } from "@/lib/options";
import { CrudManager, type CrudField } from "@/components/admin/CrudManager";
import { Badge } from "@/components/ui";

const fields: CrudField[] = [
  {
    name: "subject_id",
    label: "Subject",
    type: "select",
    required: true,
    loadOptions: loadSubjectOptions,
  },
  { name: "name", label: "Name", type: "text", required: true, placeholder: "Kinematics" },
  {
    name: "parent_topic_id",
    label: "Parent topic id",
    type: "number",
    help: "Optional. Leave blank for a top-level topic.",
  },
  { name: "sort_order", label: "Sort order", type: "number", defaultValue: "0" },
  { name: "is_active", label: "Active", type: "checkbox", editOnly: true, defaultValue: true },
  { name: "description", label: "Description", type: "textarea", colSpan: 2 },
];

export default function AdminTopicsPage() {
  return (
    <CrudManager<TopicResponse>
      title="Topics"
      description="Topics organise questions within a subject."
      addLabel="New topic"
      api={{
        list: topicsApi.list,
        create: topicsApi.create,
        update: topicsApi.update,
        remove: topicsApi.remove,
      }}
      fields={fields}
      rowKey={(r) => r.id}
      filters={[{ name: "subject_id", label: "Subject", loadOptions: loadSubjectOptions }]}
      columns={[
        { key: "name", header: "Topic", render: (r) => <span className="font-medium text-slate-900">{r.name}</span> },
        { key: "subject_id", header: "Subject", render: (r) => <span className="text-slate-500">#{r.subject_id}</span> },
        {
          key: "parent_topic_id",
          header: "Parent",
          render: (r) => (r.parent_topic_id ? `#${r.parent_topic_id}` : "—"),
        },
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
