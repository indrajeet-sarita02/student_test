"use client";

import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/guards";
import { ADMIN_NAV } from "@/lib/navigation";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth staffOnly>
      <AppShell nav={ADMIN_NAV} brand="Student Test Admin" brandHref="/admin" basePath="/admin">
        {children}
      </AppShell>
    </RequireAuth>
  );
}
