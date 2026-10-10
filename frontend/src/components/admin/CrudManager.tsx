"use client";

/**
 * Config-driven CRUD screen used by the straightforward admin resources
 * (exams, subjects, topics, users, roles …). Handles list, search, filters,
 * pagination, create/edit modal and delete confirmation. Custom resources
 * (questions, tests, assignments, …) build their own screens.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { isApiError } from "@/lib/api/client";
import type { Page } from "@/lib/types";
import { cn, fromLocalInput, toLocalInput } from "@/lib/utils";
import { useToast } from "@/components/Toast";
import { ConfirmDialog, Modal } from "@/components/Modal";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Button,
  Checkbox,
  Input,
  PageHeader,
  Pagination,
  SearchInput,
  Select,
  Textarea,
} from "@/components/ui";

type Option = { label: string; value: string | number };
type FormValue = string | boolean | number[];

export type CrudFieldType =
  | "text"
  | "email"
  | "password"
  | "number"
  | "textarea"
  | "select"
  | "multiselect"
  | "checkbox"
  | "datetime";

export interface CrudField {
  name: string;
  label: string;
  type: CrudFieldType;
  required?: boolean;
  placeholder?: string;
  help?: string;
  options?: Option[];
  loadOptions?: () => Promise<Option[]>;
  defaultValue?: FormValue;
  colSpan?: 1 | 2;
  createOnly?: boolean;
  editOnly?: boolean;
}

export interface CrudFilter {
  name: string;
  label: string;
  options?: Option[];
  loadOptions?: () => Promise<Option[]>;
}

export interface CrudApi<T> {
  list: (params: Record<string, unknown>) => Promise<Page<T>>;
  create?: (body: Record<string, unknown>) => Promise<T>;
  update?: (id: number, body: Record<string, unknown>) => Promise<T>;
  remove?: (id: number) => Promise<unknown>;
}

export interface CrudManagerProps<T> {
  title: string;
  description?: string;
  addLabel?: string;
  api: CrudApi<T>;
  fields: CrudField[];
  columns: Column<T>[];
  rowKey: (row: T) => number;
  filters?: CrudFilter[];
  toForm?: (row: T) => Record<string, FormValue>;
  canCreate?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  extraRowActions?: (row: T, reload: () => void) => React.ReactNode;
  emptyTitle?: string;
}

const PAGE_SIZE = 10;

function isNumericOption(opts: Option[]): boolean {
  return opts.length > 0 && opts.every((o) => typeof o.value === "number");
}

export function CrudManager<T>({
  title,
  description,
  addLabel = "Add new",
  api,
  fields,
  columns,
  rowKey,
  filters = [],
  toForm,
  canCreate = true,
  canEdit = true,
  canDelete = true,
  extraRowActions,
  emptyTitle,
}: CrudManagerProps<T>) {
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [data, setData] = useState<Page<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [options, setOptions] = useState<Record<string, Option[]>>({});

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<T | null>(null);
  const [form, setForm] = useState<Record<string, FormValue>>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<T | null>(null);
  const [deleting, setDeleting] = useState(false);

  const reload = useCallback(() => setRefreshKey((k) => k + 1), []);

  // `api` is typically passed as an inline object literal, so keep it in a ref
  // to avoid re-running the list effect on every render.
  const apiRef = useRef(api);
  apiRef.current = api;

  // Debounce the search box.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  // Load dynamic option lists (filters + form selects) once.
  const loadedRef = useRef(false);
  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    const loaders: Array<[string, () => Promise<Option[]>]> = [];
    for (const f of fields) if (f.loadOptions) loaders.push([f.name, f.loadOptions]);
    for (const f of filters) if (f.loadOptions) loaders.push([`filter:${f.name}`, f.loadOptions]);
    (async () => {
      const entries = await Promise.allSettled(
        loaders.map(async ([key, loader]) => [key, await loader()] as const)
      );
      const next: Record<string, Option[]> = {};
      for (const e of entries) {
        if (e.status === "fulfilled") next[e.value[0]] = e.value[1];
      }
      setOptions((prev) => ({ ...prev, ...next }));
    })();
  }, [fields, filters]);

  // Fetch the list.
  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, unknown> = {
          page,
          page_size: PAGE_SIZE,
          search: debounced || undefined,
        };
        for (const [k, v] of Object.entries(filterValues)) {
          if (v) params[k] = v;
        }
        const res = await apiRef.current.list(params);
        if (active) setData(res);
      } catch (err) {
        if (active) setError(isApiError(err) ? err.message : "Unable to load data.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [page, debounced, filterValues, refreshKey]);

  const fieldOptions = useCallback(
    (field: CrudField): Option[] => field.options ?? options[field.name] ?? [],
    [options]
  );

  const defaultForm = useMemo(() => {
    const initial: Record<string, FormValue> = {};
    for (const f of fields) {
      if (f.defaultValue !== undefined) initial[f.name] = f.defaultValue;
      else if (f.type === "checkbox") initial[f.name] = false;
      else if (f.type === "multiselect") initial[f.name] = [];
      else initial[f.name] = "";
    }
    return initial;
  }, [fields]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...defaultForm });
    setFormError(null);
    setOpen(true);
  };

  const defaultToForm = (row: T): Record<string, FormValue> => {
    const source = row as Record<string, unknown>;
    const initial: Record<string, FormValue> = {};
    for (const f of fields) {
      const raw = source[f.name];
      if (f.type === "datetime") initial[f.name] = toLocalInput(raw as string | null);
      else if (f.type === "checkbox") initial[f.name] = Boolean(raw);
      else if (f.type === "multiselect")
        initial[f.name] = Array.isArray(raw) ? (raw as number[]) : [];
      else initial[f.name] = raw === null || raw === undefined ? "" : String(raw);
    }
    return initial;
  };

  const openEdit = (row: T) => {
    setEditing(row);
    setForm((toForm ? toForm(row) : defaultToForm(row)) as Record<string, FormValue>);
    setFormError(null);
    setOpen(true);
  };

  const coerce = (field: CrudField, value: FormValue): unknown => {
    if (field.type === "checkbox") return Boolean(value);
    if (field.type === "multiselect") {
      const arr = Array.isArray(value) ? value : [];
      const opts = fieldOptions(field);
      const numeric = isNumericOption(opts);
      return numeric ? arr.map((v) => Number(v)) : arr;
    }
    if (field.type === "select") {
      const opts = fieldOptions(field);
      const numeric = isNumericOption(opts);
      if (value === "" || value === null || value === undefined) return null;
      return numeric ? Number(value) : value;
    }
    if (field.type === "number") {
      if (value === "" || value === null || value === undefined) return null;
      return Number(value);
    }
    if (field.type === "datetime") return fromLocalInput(value as string);
    if (value === "") return null;
    return value;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Basic required validation.
    for (const f of fields) {
      if (!f.required) continue;
      if (editing && f.createOnly) continue;
      if (!editing && f.editOnly) continue;
      const v = form[f.name];
      const empty =
        v === "" || v === null || v === undefined || (Array.isArray(v) && v.length === 0);
      if (empty) {
        setFormError(`${f.label} is required.`);
        return;
      }
    }

    const payload: Record<string, unknown> = {};
    for (const f of fields) {
      if (editing && f.createOnly) continue;
      if (!editing && f.editOnly) continue;
      payload[f.name] = coerce(f, form[f.name]);
    }

    setSaving(true);
    try {
      if (editing && api.update) {
        await api.update(rowKey(editing), payload);
        toast.success("Changes saved.");
      } else if (api.create) {
        await api.create(payload);
        toast.success("Created successfully.");
      }
      setOpen(false);
      reload();
    } catch (err) {
      setFormError(isApiError(err) ? err.message : "Unable to save.");
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget || !api.remove) return;
    setDeleting(true);
    try {
      await api.remove(rowKey(deleteTarget));
      toast.success("Deleted.");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to delete.");
    } finally {
      setDeleting(false);
    }
  };

  const tableColumns: Column<T>[] = useMemo(() => {
    const cols = [...columns];
    if (canEdit || canDelete || extraRowActions) {
      cols.push({
        key: "__actions",
        header: "Actions",
        align: "right",
        render: (row) => (
          <div className="flex flex-wrap items-center justify-end gap-2">
            {extraRowActions?.(row, reload)}
            {canEdit && api.update && (
              <button
                type="button"
                onClick={() => openEdit(row)}
                className="text-xs font-medium text-brand-600 hover:underline"
              >
                Edit
              </button>
            )}
            {canDelete && api.remove && (
              <button
                type="button"
                onClick={() => setDeleteTarget(row)}
                className="text-xs font-medium text-rose-600 hover:underline"
              >
                Delete
              </button>
            )}
          </div>
        ),
      });
    }
    return cols;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns, canEdit, canDelete, extraRowActions, api]);

  const activeFilterCount = Object.values(filterValues).filter(Boolean).length;

  return (
    <div>
      <PageHeader
        title={title}
        description={description}
        actions={
          canCreate && api.create ? (
            <Button onClick={openCreate}>+ {addLabel}</Button>
          ) : undefined
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <SearchInput
          value={search}
          onChange={(v) => {
            setPage(1);
            setSearch(v);
          }}
          className="w-full sm:max-w-xs"
        />
        {filters.map((f) => (
          <div key={f.name} className="w-full sm:w-44">
            <Select
              name={f.name}
              options={f.options ?? options[`filter:${f.name}`] ?? []}
              placeholder={`All ${f.label.toLowerCase()}`}
              value={filterValues[f.name] ?? ""}
              onChange={(e) => {
                setPage(1);
                setFilterValues((prev) => ({ ...prev, [f.name]: e.target.value }));
              }}
            />
          </div>
        ))}
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setFilterValues({});
              setPage(1);
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        {error ? (
          <div className="px-4 py-8 text-center text-sm text-rose-600">{error}</div>
        ) : (
          <DataTable
            columns={tableColumns}
            rows={data?.items ?? []}
            rowKey={rowKey}
            loading={loading}
            emptyTitle={emptyTitle ?? `No ${title.toLowerCase()}`}
          />
        )}
        {data && data.total > 0 && (
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            totalPages={data.total_pages}
            onPageChange={setPage}
          />
        )}
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? `Edit ${title.replace(/s$/, "")}` : `New ${title.replace(/s$/, "")}`}
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" form="crud-form" loading={saving}>
              {editing ? "Save changes" : "Create"}
            </Button>
          </>
        }
      >
        <form id="crud-form" onSubmit={submit} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {fields.map((f) => {
              const isHidden = (editing && f.createOnly) || (!editing && f.editOnly);
              if (isHidden) return null;
              const value = form[f.name];
              const wrapperClass = cn(f.colSpan === 2 && "sm:col-span-2");

              if (f.type === "textarea") {
                return (
                  <div key={f.name} className={wrapperClass}>
                    <Textarea
                      label={f.label}
                      name={f.name}
                      required={f.required}
                      help={f.help}
                      placeholder={f.placeholder}
                      value={String(value ?? "")}
                      onChange={(e) => setForm((p) => ({ ...p, [f.name]: e.target.value }))}
                    />
                  </div>
                );
              }

              if (f.type === "select") {
                return (
                  <div key={f.name} className={wrapperClass}>
                    <Select
                      label={f.label}
                      name={f.name}
                      required={f.required}
                      help={f.help}
                      options={fieldOptions(f)}
                      placeholder={f.placeholder ?? "Select…"}
                      value={String(value ?? "")}
                      onChange={(e) => setForm((p) => ({ ...p, [f.name]: e.target.value }))}
                    />
                  </div>
                );
              }

              if (f.type === "multiselect") {
                const arr = Array.isArray(value) ? value : [];
                return (
                  <div key={f.name} className={cn(wrapperClass, "sm:col-span-2")}>
                    {f.label && (
                      <p className="mb-1 text-sm font-medium text-slate-700">
                        {f.label}
                        {f.required && <span className="ml-0.5 text-rose-500">*</span>}
                      </p>
                    )}
                    <div className="max-h-56 overflow-y-auto rounded-lg border border-slate-200 p-3">
                      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                        {fieldOptions(f).map((opt) => {
                          const checked = arr.map(String).includes(String(opt.value));
                          return (
                            <Checkbox
                              key={String(opt.value)}
                              label={opt.label}
                              checked={checked}
                              onChange={() =>
                                setForm((p) => {
                                  const current = Array.isArray(p[f.name])
                                    ? (p[f.name] as number[])
                                    : [];
                                  const next = checked
                                    ? current.filter((x) => String(x) !== String(opt.value))
                                    : [...current, opt.value as number];
                                  return { ...p, [f.name]: next };
                                })
                              }
                            />
                          );
                        })}
                        {fieldOptions(f).length === 0 && (
                          <p className="text-xs text-slate-400">No options available.</p>
                        )}
                      </div>
                    </div>
                    {f.help && <p className="mt-1 text-xs text-slate-500">{f.help}</p>}
                  </div>
                );
              }

              if (f.type === "checkbox") {
                return (
                  <div key={f.name} className={cn(wrapperClass, "flex items-end pb-1")}>
                    <Checkbox
                      label={f.label}
                      checked={Boolean(value)}
                      onChange={(e) => setForm((p) => ({ ...p, [f.name]: e.target.checked }))}
                    />
                  </div>
                );
              }

              return (
                <div key={f.name} className={wrapperClass}>
                  <Input
                    label={f.label}
                    name={f.name}
                    type={
                      f.type === "datetime"
                        ? "datetime-local"
                        : f.type === "number"
                        ? "number"
                        : f.type
                    }
                    required={f.required}
                    help={f.help}
                    placeholder={f.placeholder}
                    value={String(value ?? "")}
                    onChange={(e) => setForm((p) => ({ ...p, [f.name]: e.target.value }))}
                  />
                </div>
              );
            })}
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete item?"
        message="This action cannot be undone."
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={confirmDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
