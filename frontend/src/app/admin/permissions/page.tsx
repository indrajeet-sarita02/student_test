"use client";

import { useMemo, useState } from "react";

import { permissionsApi } from "@/lib/api/endpoints";
import type { PermissionResponse } from "@/lib/types";
import { useApi } from "@/lib/hooks";
import { humanize } from "@/lib/utils";
import {
  Badge,
  Card,
  CardHeader,
  EmptyState,
  LoadingBlock,
  PageHeader,
  SearchInput,
} from "@/components/ui";

export default function AdminPermissionsPage() {
  const perms = useApi(() => permissionsApi.list());
  const [search, setSearch] = useState("");

  const grouped = useMemo(() => {
    const list = (perms.data ?? []).filter((p) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        p.name.toLowerCase().includes(q) ||
        p.code.toLowerCase().includes(q) ||
        p.module.toLowerCase().includes(q) ||
        p.action.toLowerCase().includes(q)
      );
    });
    const map = new Map<string, PermissionResponse[]>();
    for (const p of list) {
      const arr = map.get(p.module) ?? [];
      arr.push(p);
      map.set(p.module, arr);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [perms.data, search]);

  return (
    <div>
      <PageHeader
        title="Permissions"
        description="All permissions available in the system, grouped by module."
      />

      <div className="mb-4 max-w-sm">
        <SearchInput value={search} onChange={setSearch} placeholder="Search permissions…" />
      </div>

      {perms.loading ? (
        <LoadingBlock />
      ) : perms.error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-6 text-sm text-rose-700">
          {perms.error}
        </div>
      ) : grouped.length === 0 ? (
        <Card>
          <EmptyState icon="🔑" title="No permissions found" />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {grouped.map(([module, items]) => (
            <Card key={module}>
              <CardHeader
                title={humanize(module)}
                description={`${items.length} permission${items.length > 1 ? "s" : ""}`}
              />
              <ul className="divide-y divide-slate-100">
                {items.map((p) => (
                  <li key={p.id} className="flex items-start justify-between gap-3 px-4 py-2.5">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800">{p.name}</p>
                      <p className="font-mono text-[11px] text-slate-400">{p.code}</p>
                      {p.description && (
                        <p className="mt-0.5 text-xs text-slate-500">{p.description}</p>
                      )}
                    </div>
                    <Badge tone="blue">{humanize(p.action)}</Badge>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
