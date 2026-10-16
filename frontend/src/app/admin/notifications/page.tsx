"use client";

import { useState } from "react";

import { notificationsApi } from "@/lib/api/endpoints";
import type { NotificationResponse } from "@/lib/types";
import { isApiError } from "@/lib/api/client";
import { useApi } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { Modal } from "@/components/Modal";
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
  Textarea,
} from "@/components/ui";
import { loadUserOptions } from "@/lib/options";

const TYPES = ["INFO", "SUCCESS", "WARNING", "ERROR", "TEST_ASSIGNED", "RESULT_PUBLISHED"];

export default function AdminNotificationsPage() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [showAll, setShowAll] = useState(false);

  const list = useApi(
    () =>
      notificationsApi.list({
        page,
        page_size: 15,
        search: search || undefined,
        type: typeFilter || undefined,
        all: showAll ? true : undefined,
      }),
    [page, search, typeFilter, showAll]
  );

  // create / bulk state
  const [createOpen, setCreateOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [userId, setUserId] = useState("");
  const [userIds, setUserIds] = useState<number[]>([]);
  const [userOptions, setUserOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState("INFO");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const ensureUsers = async () => {
    if (userOptions.length) return;
    try {
      const opts = await loadUserOptions();
      setUserOptions(opts.map((o) => ({ label: o.label, value: Number(o.value) })));
    } catch {
      /* ignore */
    }
  };

  const openCreate = () => {
    setUserId("");
    setTitle("");
    setMessage("");
    setType("INFO");
    setFormError(null);
    setCreateOpen(true);
    void ensureUsers();
  };

  const openBulk = () => {
    setUserIds([]);
    setTitle("");
    setMessage("");
    setType("INFO");
    setFormError(null);
    setBulkOpen(true);
    void ensureUsers();
  };

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSaving(true);
    try {
      await notificationsApi.create({
        user_id: Number(userId),
        title,
        message,
        type,
      });
      toast.success("Notification sent.");
      setCreateOpen(false);
      list.reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to send notification.");
    } finally {
      setSaving(false);
    }
  };

  const submitBulk = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (userIds.length === 0) {
      setFormError("Select at least one recipient.");
      return;
    }
    setSaving(true);
    try {
      const res = await notificationsApi.bulk({
        user_ids: userIds,
        title,
        message,
        type,
      });
      toast.success(`Sent to ${res.created} user(s).`);
      setBulkOpen(false);
      list.reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to send notifications.");
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<NotificationResponse>[] = [
    {
      key: "title",
      header: "Notification",
      render: (r) => (
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-900">{r.title}</p>
          <p className="line-clamp-2 text-xs text-slate-500">{r.message}</p>
        </div>
      ),
    },
    { key: "type", header: "Type", render: (r) => <Badge tone="indigo">{r.type.replace(/_/g, " ")}</Badge> },
    {
      key: "user_id",
      header: "Recipient",
      render: (r) => <span className="text-slate-500">#{r.user_id}</span>,
    },
    {
      key: "is_read",
      header: "Read",
      render: (r) => (r.is_read ? <Badge tone="green">Read</Badge> : <Badge tone="amber">Unread</Badge>),
    },
    {
      key: "created_at",
      header: "Sent",
      render: (r) => <span className="text-xs text-slate-500">{formatDateTime(r.created_at)}</span>,
      hideOnMobile: true,
    },
  ];

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Broadcast messages to users."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={openCreate}>
              Single
            </Button>
            <Button onClick={openBulk}>+ Bulk send</Button>
          </div>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <SearchInput
          value={search}
          onChange={(v) => {
            setPage(1);
            setSearch(v);
          }}
          className="w-full sm:max-w-xs"
        />
        <div className="w-full sm:w-48">
          <Select
            name="type"
            options={TYPES.map((t) => ({ label: t.replace(/_/g, " "), value: t }))}
            placeholder="All types"
            value={typeFilter}
            onChange={(e) => {
              setPage(1);
              setTypeFilter(e.target.value);
            }}
          />
        </div>
        <Checkbox label="Show all users" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {list.error ? (
          <Alert tone="error" className="m-4">
            {list.error}
          </Alert>
        ) : (
          <DataTable
            columns={columns}
            rows={list.data?.items ?? []}
            rowKey={(r) => r.id}
            loading={list.loading}
            emptyTitle="No notifications"
          />
        )}
        {list.data && list.data.total > 0 && (
          <Pagination
            page={list.data.page}
            pageSize={list.data.page_size}
            total={list.data.total}
            totalPages={list.data.total_pages}
            onPageChange={setPage}
          />
        )}
      </div>

      {/* Create single */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Send notification"
        footer={
          <>
            <Button variant="outline" onClick={() => setCreateOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="notif-create" loading={saving}>
              Send
            </Button>
          </>
        }
      >
        <form id="notif-create" onSubmit={submitCreate} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}
          <Select
            label="Recipient"
            required
            options={userOptions}
            placeholder="Select a user"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
          <Input label="Title" required value={title} onChange={(e) => setTitle(e.target.value)} />
          <Textarea label="Message" required value={message} onChange={(e) => setMessage(e.target.value)} />
          <Select
            label="Type"
            options={TYPES.map((t) => ({ label: t.replace(/_/g, " "), value: t }))}
            value={type}
            onChange={(e) => setType(e.target.value)}
          />
        </form>
      </Modal>

      {/* Bulk */}
      <Modal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        title="Bulk send notifications"
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setBulkOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="notif-bulk" loading={saving}>
              Send to {userIds.length}
            </Button>
          </>
        }
      >
        <form id="notif-bulk" onSubmit={submitBulk} className="space-y-4">
          {formError && <Alert tone="error">{formError}</Alert>}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700">Recipients</span>
              <button
                type="button"
                className="text-xs font-medium text-brand-600 hover:underline"
                onClick={() =>
                  setUserIds(
                    userIds.length === userOptions.length ? [] : userOptions.map((o) => o.value)
                  )
                }
              >
                {userIds.length === userOptions.length ? "Clear all" : "Select all"}
              </button>
            </div>
            <div className="max-h-56 overflow-y-auto rounded-lg border border-slate-200 p-3">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {userOptions.map((o) => (
                  <Checkbox
                    key={o.value}
                    label={o.label}
                    checked={userIds.includes(o.value)}
                    onChange={(e) =>
                      setUserIds((prev) =>
                        e.target.checked ? [...prev, o.value] : prev.filter((x) => x !== o.value)
                      )
                    }
                  />
                ))}
                {userOptions.length === 0 && <p className="text-xs text-slate-400">No users.</p>}
              </div>
            </div>
          </div>
          <Input label="Title" required value={title} onChange={(e) => setTitle(e.target.value)} />
          <Textarea label="Message" required value={message} onChange={(e) => setMessage(e.target.value)} />
          <Select
            label="Type"
            options={TYPES.map((t) => ({ label: t.replace(/_/g, " "), value: t }))}
            value={type}
            onChange={(e) => setType(e.target.value)}
          />
        </form>
      </Modal>
    </div>
  );
}
