"use client";

import { useState } from "react";

import { auditLogsApi } from "@/lib/api/endpoints";
import type { AuditLogResponse } from "@/lib/types";
import { useApi } from "@/lib/hooks";
import { formatDateTime, humanize } from "@/lib/utils";
import { Modal } from "@/components/Modal";
import {
  Alert,
  Button,
  Card,
  Input,
  PageHeader,
  Pagination,
  Select,
} from "@/components/ui";
import { DataTable, type Column } from "@/components/DataTable";

export default function AdminAuditLogsPage() {
  const [page, setPage] = useState(1);
  const [moduleFilter, setModuleFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [entityType, setEntityType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [target, setTarget] = useState<AuditLogResponse | null>(null);

  const params = {
    page,
    page_size: 15,
    module: moduleFilter || undefined,
    action: actionFilter || undefined,
    entity_type: entityType || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  };

  const logs = useApi(() => auditLogsApi.list(params), [page, moduleFilter, actionFilter, entityType, dateFrom, dateTo]);

  const columns: Column<AuditLogResponse>[] = [
    {
      key: "created_at",
      header: "When",
      render: (r) => <span className="whitespace-nowrap text-xs text-slate-500">{formatDateTime(r.created_at)}</span>,
    },
    {
      key: "username",
      header: "User",
      render: (r) => r.username ?? (r.user_id ? `#${r.user_id}` : "system"),
    },
    {
      key: "module",
      header: "Module",
      render: (r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{humanize(r.module)}</p>
          <p className="text-xs text-slate-400">{r.action}</p>
        </div>
      ),
    },
    {
      key: "entity",
      header: "Entity",
      render: (r) => (r.entity_type ? `${r.entity_type}${r.entity_id ? ` #${r.entity_id}` : ""}` : "—"),
      hideOnMobile: true,
    },
    {
      key: "ip_address",
      header: "IP",
      render: (r) => r.ip_address ?? "—",
      hideOnMobile: true,
    },
    {
      key: "view",
      header: "",
      align: "right",
      render: (r) => (
        <button
          type="button"
          onClick={() => setTarget(r)}
          className="text-xs font-medium text-brand-600 hover:underline"
        >
          Details
        </button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="Audit Logs" description="A record of administrative and system actions." />

      <Card className="mb-4 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Input label="Module" value={moduleFilter} onChange={(e) => setModuleFilter(e.target.value)} placeholder="e.g. user" />
          <Input label="Action" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} placeholder="e.g. create" />
          <Input label="Entity type" value={entityType} onChange={(e) => setEntityType(e.target.value)} placeholder="e.g. test" />
          <Input label="From" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <Input label="To" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
        {(moduleFilter || actionFilter || entityType || dateFrom || dateTo) && (
          <button
            type="button"
            onClick={() => {
              setModuleFilter("");
              setActionFilter("");
              setEntityType("");
              setDateFrom("");
              setDateTo("");
              setPage(1);
            }}
            className="mt-3 text-xs font-medium text-brand-600 hover:underline"
          >
            Clear filters
          </button>
        )}
      </Card>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {logs.error ? (
          <Alert tone="error" className="m-4">
            {logs.error}
          </Alert>
        ) : (
          <DataTable
            columns={columns}
            rows={logs.data?.items ?? []}
            rowKey={(r) => r.id}
            loading={logs.loading}
            emptyTitle="No audit logs"
          />
        )}
        {logs.data && logs.data.total > 0 && (
          <Pagination
            page={logs.data.page}
            pageSize={logs.data.page_size}
            total={logs.data.total}
            totalPages={logs.data.total_pages}
            onPageChange={setPage}
          />
        )}
      </div>

      <Modal
        open={Boolean(target)}
        onClose={() => setTarget(null)}
        title="Audit log detail"
        size="lg"
        footer={
          <Button variant="outline" onClick={() => setTarget(null)}>
            Close
          </Button>
        }
      >
        {target && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs uppercase text-slate-400">Module</p>
                <p className="text-slate-800">{humanize(target.module)}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-400">Action</p>
                <p className="text-slate-800">{target.action}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-400">User</p>
                <p className="text-slate-800">{target.username ?? (target.user_id ? `#${target.user_id}` : "system")}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-400">Entity</p>
                <p className="text-slate-800">
                  {target.entity_type ?? "—"}
                  {target.entity_id ? ` #${target.entity_id}` : ""}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-400">IP address</p>
                <p className="text-slate-800">{target.ip_address ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-400">When</p>
                <p className="text-slate-800">{formatDateTime(target.created_at)}</p>
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase text-slate-400">Old data</p>
              <pre className="max-h-48 overflow-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                {JSON.stringify(target.old_data, null, 2) ?? "—"}
              </pre>
            </div>
            <div>
              <p className="mb-1 text-xs uppercase text-slate-400">New data</p>
              <pre className="max-h-48 overflow-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                {JSON.stringify(target.new_data, null, 2) ?? "—"}
              </pre>
            </div>
            {target.user_agent && (
              <div>
                <p className="text-xs uppercase text-slate-400">User agent</p>
                <p className="break-all text-xs text-slate-500">{target.user_agent}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
