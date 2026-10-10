"use client";

import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/guards";
import { MAIN_NAV } from "@/lib/navigation";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppShell nav={MAIN_NAV} brand="Student Test" brandHref="/" basePath="">
        {children}
      </AppShell>
    </RequireAuth>
  );
}
