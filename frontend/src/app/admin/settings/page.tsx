"use client";

import { useState } from "react";

import { settingsApi } from "@/lib/api/endpoints";
import type { SettingResponse } from "@/lib/types";
import { isApiError } from "@/lib/api/client";
import { useApi } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { Modal } from "@/components/Modal";
import {
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  EmptyState,
  Input,
  LoadingBlock,
  PageHeader,
  SearchInput,
  Textarea,
} from "@/components/ui";

export default function AdminSettingsPage() {
  const toast = useToast();
  const settings = useApi(() => settingsApi.list());
  const [search, setSearch] = useState("");
  const [target, setTarget] = useState<SettingResponse | null>(null);
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openEdit = (s: SettingResponse) => {
    setTarget(s);
    setValue(s.setting_value ?? "");
    setDescription(s.description ?? "");
    setIsPublic(s.is_public);
    setError(null);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target) return;
    setSaving(true);
    setError(null);
    try {
      await settingsApi.update(target.setting_key, {
        setting_value: value,
        description: description || null,
        is_public: isPublic,
      });
      toast.success("Setting saved.");
      setTarget(null);
      settings.reload();
    } catch (err) {
      setError(isApiError(err) ? err.message : "Unable to save setting.");
    } finally {
      setSaving(false);
    }
  };

  const items = (settings.data ?? []).filter((s) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.setting_key.toLowerCase().includes(q) || (s.description ?? "").toLowerCase().includes(q);
  });

  return (
    <div>
      <PageHeader title="Settings" description="Application configuration values." />

      <div className="mb-4 max-w-sm">
        <SearchInput value={search} onChange={setSearch} placeholder="Search settings…" />
      </div>

      {settings.loading ? (
        <LoadingBlock />
      ) : settings.error ? (
        <Alert tone="error">{settings.error}</Alert>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState icon="⚙️" title="No settings found" />
        </Card>
      ) : (
        <Card>
          <div className="divide-y divide-slate-100">
            {items.map((s) => (
              <div
                key={s.id}
                className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-mono text-sm font-medium text-slate-900">{s.setting_key}</p>
                    {s.is_public ? <Badge tone="green">Public</Badge> : <Badge tone="slate">Private</Badge>}
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">
                    {s.description ?? "No description"}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-400">
                    Updated {s.updated_by ? `by #${s.updated_by} ` : ""}
                    {formatDateTime(s.updated_at)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <code className="max-w-[220px] truncate rounded bg-slate-50 px-2 py-1 text-xs text-slate-600">
                    {s.setting_value ?? "—"}
                  </code>
                  <Button size="sm" variant="outline" onClick={() => openEdit(s)}>
                    Edit
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Modal
        open={Boolean(target)}
        onClose={() => setTarget(null)}
        title={`Edit — ${target?.setting_key ?? ""}`}
        footer={
          <>
            <Button variant="outline" onClick={() => setTarget(null)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="setting-form" loading={saving}>
              Save
            </Button>
          </>
        }
      >
        <form id="setting-form" onSubmit={save} className="space-y-4">
          {error && <Alert tone="error">{error}</Alert>}
          <Input
            label="Key"
            value={target?.setting_key ?? ""}
            readOnly
            className="bg-slate-100"
          />
          <Textarea
            label="Value"
            name="setting_value"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          <Textarea
            label="Description"
            name="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Checkbox
            label="Public (visible to unauthenticated clients)"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
        </form>
      </Modal>
    </div>
  );
}
