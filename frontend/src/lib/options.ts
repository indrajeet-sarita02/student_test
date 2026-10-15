"use client";

// Reusable async loaders that turn list endpoints into <select> options.

import { examsApi, permissionsApi, rolesApi, subjectsApi, usersApi } from "@/lib/api/endpoints";
import { humanize } from "@/lib/utils";

export interface Option {
  label: string;
  value: string | number;
}

const BIG = 100;

export async function loadExamOptions(): Promise<Option[]> {
  const res = await examsApi.list({ page_size: BIG, sort_by: "name", sort_order: "asc" });
  return res.items.map((e) => ({ label: e.name, value: e.id }));
}

export async function loadSubjectOptions(): Promise<Option[]> {
  const res = await subjectsApi.list({ page_size: BIG, sort_by: "name", sort_order: "asc" });
  return res.items.map((s) => ({ label: s.name, value: s.id }));
}

export async function loadRoleOptions(): Promise<Option[]> {
  const res = await rolesApi.list({ page_size: BIG, sort_by: "name", sort_order: "asc" });
  return res.items.map((r) => ({ label: r.name, value: r.id }));
}

export async function loadPermissionOptions(): Promise<Option[]> {
  const res = await permissionsApi.list();
  return res.map((p) => ({ label: `${humanize(p.module)} · ${humanize(p.action)}`, value: p.id }));
}

export async function loadUserOptions(): Promise<Option[]> {
  const res = await usersApi.list({ page_size: BIG, sort_by: "username", sort_order: "asc" });
  return res.items.map((u) => ({ label: `${u.username} (${u.email})`, value: u.id }));
}


