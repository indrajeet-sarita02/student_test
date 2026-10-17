"use client";

import { useEffect, useState } from "react";

import { usersApi } from "@/lib/api/endpoints";
import type { UserResponse } from "@/lib/types";
import { isApiError } from "@/lib/api/client";
import { useToast } from "@/components/Toast";
import { CrudManager, type CrudField } from "@/components/admin/CrudManager";
import { Modal } from "@/components/Modal";
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Input,
  Label,
  Select,
  StatusBadge,
} from "@/components/ui";
import { loadRoleOptions } from "@/lib/options";
import { formatDateTime } from "@/lib/utils";
import { useAuth } from "@/lib/auth/auth-context";

const STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "PENDING"];

const fields: CrudField[] = [
  { name: "username", label: "Username", type: "text", required: true, createOnly: true },
  { name: "email", label: "Email", type: "email", required: true },
  {
    name: "password",
    label: "Password",
    type: "password",
    help: "Required on create. On edit, leave blank to keep unchanged.",
  },
  { name: "first_name", label: "First name", type: "text" },
  { name: "last_name", label: "Last name", type: "text" },
  { name: "mobile", label: "Mobile", type: "text" },
  {
    name: "status",
    label: "Status",
    type: "select",
    createOnly: true,
    defaultValue: "ACTIVE",
    options: STATUSES.map((s) => ({ label: s, value: s })),
  },
  {
    name: "role_ids",
    label: "Roles",
    type: "multiselect",
    createOnly: true,
    loadOptions: loadRoleOptions,
  },
  { name: "is_verified", label: "Verified", type: "checkbox" },
];

export default function AdminUsersPage() {
  const toast = useToast();
  const { hasPermission } = useAuth();
  const [roleTarget, setRoleTarget] = useState<UserResponse | null>(null);
  const [statusTarget, setStatusTarget] = useState<UserResponse | null>(null);
  const [resetTarget, setResetTarget] = useState<UserResponse | null>(null);
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetTemp, setResetTemp] = useState<string | null>(null);
  const [roleOptions, setRoleOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [selectedRoles, setSelectedRoles] = useState<number[]>([]);
  const [newStatus, setNewStatus] = useState("ACTIVE");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadRoleOptions()
      .then((opts) => setRoleOptions(opts.map((o) => ({ label: o.label, value: Number(o.value) }))))
      .catch(() => setRoleOptions([]));
  }, []);

  const openRoles = (u: UserResponse) => {
    setRoleTarget(u);
    setSelectedRoles(u.roles.map((r) => r.id));
  };

  const openReset = (u: UserResponse) => {
    setResetTarget(u);
    setResetNewPassword("");
    setResetTemp(null);
  };

  const saveRoles = async () => {
    if (!roleTarget) return;
    setSaving(true);
    try {
      await usersApi.assignRoles(roleTarget.id, selectedRoles);
      toast.success("Roles updated.");
      setRoleTarget(null);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to update roles.");
    } finally {
      setSaving(false);
    }
  };

  const saveStatus = async () => {
    if (!statusTarget) return;
    setSaving(true);
    try {
      await usersApi.setStatus(statusTarget.id, newStatus);
      toast.success("Status updated.");
      setStatusTarget(null);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to update status.");
    } finally {
      setSaving(false);
    }
  };

  const submitReset = async () => {
    if (!resetTarget) return;
    setSaving(true);
    setResetTemp(null);
    try {
      const body: { new_password?: string } = {};
      if (resetNewPassword.trim()) body.new_password = resetNewPassword.trim();
      const res = await usersApi.resetPassword(resetTarget.id, body.new_password);
      setResetTemp(res.temporary_password);
      if (!res.temporary_password) toast.success("Password reset.");
      else toast.success("Temporary password generated.");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to reset password.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <CrudManager<UserResponse>
        title="Users"
        description="Create and manage platform users."
        addLabel="New user"
        api={{
          list: usersApi.list,
          create: usersApi.create,
          update: usersApi.update,
          remove: usersApi.remove,
        }}
        fields={fields}
        rowKey={(r) => r.id}
        filters={[
          {
            name: "status",
            label: "Status",
            options: STATUSES.map((s) => ({ label: s, value: s })),
          },
          { name: "role_id", label: "Role", loadOptions: loadRoleOptions },
        ]}
        columns={[
          {
            key: "username",
            header: "User",
            render: (r) => (
              <div>
                <p className="font-medium text-slate-900">{r.username}</p>
                <p className="text-xs text-slate-400">{r.email}</p>
              </div>
            ),
          },
          {
            key: "name",
            header: "Name",
            render: (r) => [r.first_name, r.last_name].filter(Boolean).join(" ") || "—",
            hideOnMobile: true,
          },
          {
            key: "roles",
            header: "Roles",
            render: (r) => (
              <div className="flex flex-wrap gap-1">
                {r.roles.length ? (
                  r.roles.map((role) => (
                    <Badge key={role.id} tone="indigo">
                      {role.code}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">No roles</span>
                )}
              </div>
            ),
          },
          { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
          {
            key: "last_login_at",
            header: "Last login",
            render: (r) => <span className="text-xs text-slate-500">{formatDateTime(r.last_login_at)}</span>,
            hideOnMobile: true,
          },
        ]}
        extraRowActions={(row) => (
          <>
            <button
              type="button"
              onClick={() => openRoles(row)}
              className="text-xs font-medium text-indigo-600 hover:underline"
            >
              Roles
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusTarget(row);
                setNewStatus(row.status);
              }}
              className="text-xs font-medium text-amber-600 hover:underline"
            >
              Status
            </button>
            {hasPermission("user.update") && (
              <button
                type="button"
                onClick={() => openReset(row)}
                className="text-xs font-medium text-violet-600 hover:underline"
              >
                Reset password
              </button>
            )}
          </>
        )}
      />

      <Modal
        open={Boolean(roleTarget)}
        onClose={() => setRoleTarget(null)}
        title={`Roles — ${roleTarget?.username ?? ""}`}
        footer={
          <>
            <Button variant="outline" onClick={() => setRoleTarget(null)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={saveRoles} loading={saving}>
              Save
            </Button>
          </>
        }
      >
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {roleOptions.map((opt) => (
            <Checkbox
              key={opt.value}
              label={opt.label}
              checked={selectedRoles.includes(opt.value)}
              onChange={(e) =>
                setSelectedRoles((prev) =>
                  e.target.checked ? [...prev, opt.value] : prev.filter((x) => x !== opt.value)
                )
              }
            />
          ))}
          {roleOptions.length === 0 && <p className="text-sm text-slate-500">No roles found.</p>}
        </div>
      </Modal>

      <Modal
        open={Boolean(statusTarget)}
        onClose={() => setStatusTarget(null)}
        title={`Change status — ${statusTarget?.username ?? ""}`}
        footer={
          <>
            <Button variant="outline" onClick={() => setStatusTarget(null)} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={saveStatus} loading={saving}>
              Save
            </Button>
          </>
        }
      >
        <Select
          name="status"
          label="Status"
          options={STATUSES.map((s) => ({ label: s, value: s }))}
          value={newStatus}
          onChange={(e) => setNewStatus(e.target.value)}
        />
      </Modal>

      <Modal
        open={Boolean(resetTarget)}
        onClose={() => {
          setResetTarget(null);
          setResetTemp(null);
        }}
        title={`Reset password — ${resetTarget?.username ?? ""}`}
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setResetTarget(null);
                setResetTemp(null);
              }}
              disabled={saving}
            >
              Close
            </Button>
            <Button onClick={submitReset} loading={saving} disabled={!!resetTemp}>
              {resetNewPassword.trim() ? "Set password" : "Generate temporary password"}
            </Button>
          </>
        }
      >
        {resetTemp ? (
          <div className="space-y-3">
            <Alert tone="success">
              Temporary password generated. Share it with the user securely — it will not be shown again.
            </Alert>
            <div>
              <Label>Temporary password</Label>
              <div className="mt-1 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 font-mono text-sm tracking-widest text-emerald-700">
                {resetTemp}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <Alert tone="info">
              Leave the field empty to generate a one-time temporary password. Otherwise provide a new password for the user.
            </Alert>
            <Input
              label="New password (optional)"
              type="password"
              value={resetNewPassword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setResetNewPassword(e.target.value)}
            />
          </div>
        )}
      </Modal>
    </>
  );
}
