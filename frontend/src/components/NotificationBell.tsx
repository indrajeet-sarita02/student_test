"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { notificationsApi } from "@/lib/api/endpoints";
import { useAuth } from "@/lib/auth/auth-context";
import type { NotificationResponse } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export function NotificationBell({ basePath = "" }: { basePath?: string }) {
  const { user } = useAuth();
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    const load = async () => {
      try {
        const res = await notificationsApi.unreadCount();
        if (active) setCount(res.count);
      } catch {
        /* ignore */
      }
    };
    load();
    const timer = setInterval(load, 60000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [user]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      try {
        const res = await notificationsApi.list({ page: 1, page_size: 5 });
        setItems(res.items);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
  };

  if (!user) return null;

  const target = `${basePath}/notifications`;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={toggle}
        className="relative rounded-full p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
        aria-label="Notifications"
      >
        🔔
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
            <span className="text-sm font-semibold text-slate-800">Notifications</span>
            <Link
              href={target}
              onClick={() => setOpen(false)}
              className="text-xs font-medium text-brand-600 hover:underline"
            >
              View all
            </Link>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <p className="px-3 py-6 text-center text-xs text-slate-500">Loading…</p>
            ) : items.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-slate-500">No notifications</p>
            ) : (
              items.map((n) => (
                <Link
                  key={n.id}
                  href={target}
                  onClick={() => setOpen(false)}
                  className="block border-b border-slate-50 px-3 py-2 last:border-0 hover:bg-slate-50"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-slate-800">
                      {n.title}
                    </span>
                    {!n.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-brand-500" />}
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.message}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">
                    {formatDateTime(n.created_at)}
                  </p>
                </Link>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
