"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth, RequirePermission } from "@/components/guards";
import { ADMIN_NAV } from "@/lib/navigation";
import { requiredPermissionFor } from "@/lib/route-permissions";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const required = requiredPermissionFor(pathname);

  return (
    <RequireAuth staffOnly>
      <RequirePermission
        permission={required?.permission}
        anyOf={required?.anyOf}
      >
        <AppShell
          nav={ADMIN_NAV}
          brand="Student Test Admin"
          brandHref="/admin"
          basePath="/admin"
        >
          {children}
        </AppShell>
      </RequirePermission>
    </RequireAuth>
  );
}
