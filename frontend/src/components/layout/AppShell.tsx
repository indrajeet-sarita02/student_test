"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth/auth-context";
import { cn, initials } from "@/lib/utils";
import type { NavGroup } from "@/lib/navigation";
import { NotificationBell } from "@/components/NotificationBell";

export function AppShell({
  nav,
  brand,
  brandHref,
  basePath = "",
  children,
}: {
  nav: NavGroup[];
  brand: string;
  brandHref: string;
  basePath?: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, hasPermission, logout, isStaff } = useAuth();
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setOpen(false);
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const isActive = (href: string) => {
    if (href === "/" || href === "/admin") return pathname === href;
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const groups = nav
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => !item.permission || hasPermission(item.permission)),
    }))
    .filter((group) => group.items.length > 0);

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.username || "User";

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-4">
        <span className="text-lg">🎯</span>
        <span className="truncate text-sm font-bold text-slate-900">{brand}</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {groups.map((group) => (
          <div key={group.section} className="mb-4">
            <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {group.section}
            </p>
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      isActive(item.href)
                        ? "bg-brand-50 text-brand-700"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    )}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span className="truncate">{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <div className="border-t border-slate-200 p-3">
        <div className="flex items-center gap-2 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
            {initials(displayName)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-slate-800">{displayName}</p>
            <p className="truncate text-[10px] text-slate-500">
              {user?.roles?.map((r) => r.code).join(", ") || "—"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        {sidebar}
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 max-w-[85vw] border-r border-slate-200 bg-white shadow-xl">
            {sidebar}
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/90 px-3 backdrop-blur sm:px-4">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Open menu"
          >
            ☰
          </button>
          <Link href={brandHref} className="flex items-center gap-2 lg:hidden">
            <span>🎯</span>
            <span className="text-sm font-bold text-slate-900">{brand}</span>
          </Link>
          <div className="hidden flex-1 lg:block" />
          <div className="ml-auto flex items-center gap-1">
            {isStaff && (
              <Link
                href={basePath === "/admin" ? "/" : "/admin"}
                className="hidden rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 sm:inline-block"
              >
                {basePath === "/admin" ? "Student view" : "Admin panel"}
              </Link>
            )}
            <NotificationBell basePath={basePath} />
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 rounded-full p-1 hover:bg-slate-100"
                aria-label="Account menu"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
                  {initials(displayName)}
                </span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
                  <div className="border-b border-slate-100 px-3 py-2">
                    <p className="truncate text-sm font-semibold text-slate-800">{displayName}</p>
                    <p className="truncate text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <Link
                    href={`${basePath}/profile`}
                    className="block px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    👤 Profile
                  </Link>
                  <button
                    type="button"
                    onClick={logout}
                    className="block w-full px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
                  >
                    ⏻ Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-3 py-5 sm:px-5 sm:py-6">{children}</main>
      </div>
    </div>
  );
}
