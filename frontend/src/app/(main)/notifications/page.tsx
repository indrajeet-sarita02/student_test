"use client";

import { useState } from "react";

import { notificationsApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { isApiError } from "@/lib/api/client";
import { cn, formatDateTime } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  LoadingBlock,
  PageHeader,
  Pagination,
} from "@/components/ui";

const TYPE_TONE: Record<string, "blue" | "green" | "amber" | "red" | "indigo" | "purple"> = {
  INFO: "blue",
  SUCCESS: "green",
  WARNING: "amber",
  ERROR: "red",
  TEST_ASSIGNED: "indigo",
  RESULT_PUBLISHED: "purple",
};

export default function NotificationsPage() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const list = useApi(
    () => notificationsApi.list({ page, page_size: pageSize }),
    [page]
  );
  const [busy, setBusy] = useState(false);

  const items = list.data?.items ?? [];
  const unread = items.filter((n) => !n.is_read).length;

  const markRead = async (id: number) => {
    try {
      await notificationsApi.markRead(id);
      list.setData((prev) =>
        prev
          ? { ...prev, items: prev.items.map((n) => (n.id === id ? { ...n, is_read: true } : n)) }
          : prev
      );
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to mark as read.");
    }
  };

  const readAll = async () => {
    setBusy(true);
    try {
      await notificationsApi.readAll();
      list.reload();
      toast.success("All notifications marked as read.");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to mark all as read.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Notifications"
        description={unread > 0 ? `${unread} unread on this page` : "You're all caught up."}
        actions={
          <Button variant="outline" size="sm" onClick={readAll} disabled={busy}>
            Mark all read
          </Button>
        }
      />

      {list.loading ? (
        <LoadingBlock />
      ) : list.error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-6 text-sm text-rose-700">
          {list.error}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState icon="🔔" title="No notifications" description="You have no notifications yet." />
        </Card>
      ) : (
        <Card>
          <ul className="divide-y divide-slate-100">
            {items.map((n) => (
              <li
                key={n.id}
                className={cn(
                  "flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-start sm:justify-between",
                  !n.is_read && "bg-brand-50/40"
                )}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    {!n.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-brand-500" />}
                    <p className="truncate text-sm font-semibold text-slate-900">{n.title}</p>
                    <Badge tone={TYPE_TONE[n.type] ?? "slate"}>{n.type.replace(/_/g, " ")}</Badge>
                  </div>
                  <p className="mt-1 whitespace-pre-line text-sm text-slate-600">{n.message}</p>
                  <p className="mt-1 text-xs text-slate-400">{formatDateTime(n.created_at)}</p>
                </div>
                {!n.is_read && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => markRead(n.id)}
                    className="self-start"
                  >
                    Mark read
                  </Button>
                )}
              </li>
            ))}
          </ul>
          {list.data && list.data.total > 0 && (
            <Pagination
              page={list.data.page}
              pageSize={list.data.page_size}
              total={list.data.total}
              totalPages={list.data.total_pages}
              onPageChange={setPage}
            />
          )}
        </Card>
      )}
    </div>
  );
}
