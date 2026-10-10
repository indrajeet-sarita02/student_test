"use client";

import { useMemo, useState } from "react";

import { permissionsApi, rolesApi } from "@/lib/api/endpoints";
import type { RoleResponse } from "@/lib/types";
import { isApiError } from "@/lib/api/client";
import { humanize } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { CrudManager, type CrudField } from "@/components/admin/CrudManager";
import { Modal } from "@/components/Modal";
import { Badge, Button, Checkbox } from "@/components/ui";

const fields: CrudField[] = [
  { name: "name", label: "Name", type: "text", required: true, placeholder: "Content Manager" },
  { name: "code", label: "Code", type: "text", required: true, createOnly: true, placeholder: "CONTENT_MANAGER" },
  { name: "is_active", label: "Active", type: "checkbox", defaultValue: true },
  { name: "description", label: "Description", type: "textarea", colSpan: 2 },
];

export default function AdminRolesPage() {
  const toast = useToast();
  const [permTarget, setPermTarget] = useState<RoleResponse | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [loadingPerms, setLoadingPerms] = useState(false);
  const [saving, setSaving] = useState(false);
  const [modules, setModules] = useState<Array<{ name: string; permissions: Array<{ id: number; label: string }> }>>([]);

  const openPermissions = async (role: RoleResponse) => {
    setPermTarget(role);
    setSelected(role.permissions.map((p) => p.id));
    setLoadingPerms(true);
    try {
      const res = await permissionsApi.modules();
      const grouped = res.map((m) => ({
        name: String(m.module),
        permissions: (m.permissions ?? []).map((p) => ({
          id: p.id,
          label: humanize(p.name ?? p.code),
        })),
      }));
      if (grouped.length) setModules(grouped);
      else {
        const all = await permissionsApi.list();
        const map = new Map<string, Array<{ id: number; label: string }>>();
        for (const p of all) {
          const arr = map.get(p.module) ?? [];
          arr.push({ id: p.id, label: humanize(p.action) });
          map.set(p.module, arr);
        }
        setModules([...map.entries()].map(([name, permissions]) => ({ name, permissions })));
      }
    } catch {
      try {
        const all = await permissionsApi.list();
        const map = new Map<string, Array<{ id: number; label: string }>>();
        for (const p of all) {
          const arr = map.get(p.module) ?? [];
          arr.push({ id: p.id, label: humanize(p.action) });
          map.set(p.module, arr);
        }
        setModules([...map.entries()].map(([name, permissions]) => ({ name, permissions })));
      } catch (err) {
        toast.error(isApiError(err) ? err.message : "Unable to load permissions.");
      }
    } finally {
      setLoadingPerms(false);
    }
  };

  const toggle = (id: number, checked: boolean) => {
    setSelected((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
  };

  const savePermissions = async () => {
    if (!permTarget) return;
    setSaving(true);
    try {
      await rolesApi.setPermissions(permTarget.id, selected);
      toast.success("Permissions updated.");
      setPermTarget(null);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to update permissions.");
    } finally {
      setSaving(false);
    }
  };

  const total = useMemo(() => modules.reduce((n, m) => n + m.permissions.length, 0), [modules]);

  return (
    <>
      <CrudManager<RoleResponse>
        title="Roles"
        description="Roles bundle permissions. Assign them to users."
        addLabel="New role"
        api={{
          list: rolesApi.list,
          create: rolesApi.create,
          update: rolesApi.update,
          remove: rolesApi.remove,
        }}
        fields={fields}
        rowKey={(r) => r.id}
        columns={[
          {
            key: "name",
            header: "Role",
            render: (r) => (
              <div>
                <p className="font-medium text-slate-900">{r.name}</p>
                <p className="text-xs text-slate-400">{r.code}</p>
              </div>
            ),
          },
          {
            key: "permissions",
            header: "Permissions",
            render: (r) => <Badge tone="indigo">{r.permissions.length}</Badge>,
          },
          {
            key: "is_system_role",
            header: "System",
            render: (r) => (r.is_system_role ? <Badge tone="amber">System</Badge> : "—"),
          },
          {
            key: "is_active",
            header: "Active",
            render: (r) => <Badge tone={r.is_active ? "green" : "slate"}>{r.is_active ? "Yes" : "No"}</Badge>,
          },
        ]}
        extraRowActions={(row) => (
          <button
            type="button"
            onClick={() => openPermissions(row)}
            className="text-xs font-medium text-indigo-600 hover:underline"
          >
            Permissions
          </button>
        )}
      />

      <Modal
        open={Boolean(permTarget)}
        onClose={() => setPermTarget(null)}
        title={`Permissions — ${permTarget?.name ?? ""}`}
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setPermTarget(null)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={savePermissions} loading={saving} disabled={loadingPerms}>
              Save ({selected.length})
            </Button>
          </>
        }
      >
        {loadingPerms ? (
          <p className="py-6 text-center text-sm text-slate-500">Loading permissions…</p>
        ) : (
          <div className="space-y-4">
            <p className="text-xs text-slate-500">{total} permissions available</p>
            {modules.map((m) => (
              <div key={m.name}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {humanize(m.name)}
                </p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {m.permissions.map((p) => (
                    <Checkbox
                      key={p.id}
                      label={p.label}
                      checked={selected.includes(p.id)}
                      onChange={(e) => toggle(p.id, e.target.checked)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </>
  );
}
