"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth/auth-context";
import { notificationsApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import {
  Badge,
  Card,
  CardHeader,
  EmptyState,
  LoadingBlock,
  PageHeader,
  StatCard,
} from "@/components/ui";

export default function DashboardPage() {
  const { user } = useAuth();
  const notifications = useApi(() => notificationsApi.list({ page: 1, page_size: 5 }));
  const unread = useApi(() => notificationsApi.unreadCount());

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.username || "there";

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${displayName}`}
        description="Here is an overview of your activity."
      />

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard
          label="Notifications"
          value={notifications.data?.total ?? 0}
          icon="🔔"
          hint={`${unread.data?.count ?? 0} unread`}
        />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Recent notifications"
            actions={
              <Link
                href="/notifications"
                className="text-xs font-medium text-brand-600 hover:underline"
              >
                View all
              </Link>
            }
          />
          {notifications.loading ? (
            <LoadingBlock />
          ) : notifications.error ? (
            <div className="px-4 py-6 text-sm text-rose-600">{notifications.error}</div>
          ) : (notifications.data?.items ?? []).length === 0 ? (
            <EmptyState title="No notifications" description="You're all caught up." icon="🔔" />
          ) : (
            <ul className="divide-y divide-slate-100">
              {notifications.data!.items.map((n) => (
                <li key={n.id} className="px-4 py-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium text-slate-800">{n.title}</p>
                    {!n.is_read && <Badge tone="indigo">New</Badge>}
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.message}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">
                    {formatDateTime(n.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader title="Your account" />
          <div className="space-y-3 px-4 py-4 text-sm text-slate-600">
            <p>
              Signed in as <span className="font-medium text-slate-800">{user?.email}</span>.
            </p>
            <Link
              href="/profile"
              className="inline-block text-sm font-medium text-brand-600 hover:underline"
            >
              View profile →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
