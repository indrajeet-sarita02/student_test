// Test lifecycle helpers. The backend is authoritative for every transition;
// these describe which action buttons the UI may show for a given status.
//
// DRAFT -> READY -> PUBLISHED -> SCHEDULED/ACTIVE -> COMPLETED -> ARCHIVED
// (a PUBLISHED test can also be CLOSED directly).

import type { TestStatus } from "@/lib/types";

import type { TestStatus as TestStatusType } from "@/lib/types";

export type TestLifecycleAction =
  | "ready"
  | "publish"
  | "schedule"
  | "activate"
  | "complete"
  | "archive"
  | "close";

export interface LifecycleActionMeta {
  action: TestLifecycleAction;
  label: string;
  /** Resulting status once the action succeeds. */
  to: TestStatusType;
  variant: "primary" | "secondary" | "danger";
}

const ACTIONS: Record<TestStatusType, LifecycleActionMeta[]> = {
  DRAFT: [
    { action: "ready", label: "Mark Ready", to: "READY", variant: "secondary" },
    { action: "publish", label: "Publish", to: "PUBLISHED", variant: "primary" },
  ],
  READY: [
    { action: "publish", label: "Publish", to: "PUBLISHED", variant: "primary" },
  ],
  PUBLISHED: [
    { action: "schedule", label: "Schedule", to: "SCHEDULED", variant: "secondary" },
    { action: "activate", label: "Activate", to: "ACTIVE", variant: "primary" },
    { action: "close", label: "Close", to: "CLOSED", variant: "danger" },
  ],
  SCHEDULED: [
    { action: "activate", label: "Activate", to: "ACTIVE", variant: "primary" },
    { action: "complete", label: "Complete", to: "COMPLETED", variant: "secondary" },
  ],
  ACTIVE: [
    { action: "complete", label: "Complete", to: "COMPLETED", variant: "secondary" },
  ],
  COMPLETED: [
    { action: "archive", label: "Archive", to: "ARCHIVED", variant: "secondary" },
  ],
  CLOSED: [
    { action: "archive", label: "Archive", to: "ARCHIVED", variant: "secondary" },
  ],
  ARCHIVED: [],
};

/** Actions legal for the current test status (drives button visibility). */
export function lifecycleActions(status: string): LifecycleActionMeta[] {
  return ACTIONS[status as TestStatusType] ?? [];
}

/** Human-readable label for a raw status code. */
export function testStatusLabel(status: string): string {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Tailwind classes for a status badge. */
export function testStatusTone(status: string): string {
  switch (status) {
    case "PUBLISHED":
    case "ACTIVE":
      return "bg-emerald-100 text-emerald-700";
    case "SCHEDULED":
      return "bg-sky-100 text-sky-700";
    case "READY":
      return "bg-indigo-100 text-indigo-700";
    case "COMPLETED":
      return "bg-blue-100 text-blue-700";
    case "CLOSED":
      return "bg-amber-100 text-amber-700";
    case "ARCHIVED":
      return "bg-slate-200 text-slate-600";
    default:
      return "bg-slate-100 text-slate-600";
  }
}
