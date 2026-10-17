// Maps an admin pathname to the permission(s) it requires. Derived from
// ADMIN_NAV so the sidebar and the route guard can never drift apart.
//
// The backend is still authoritative — this only drives the client-side
// redirect to /403 and the visibility of action buttons.

import { ADMIN_NAV } from "@/lib/navigation";
import { hasAnyPermission } from "@/lib/permissions";

export interface RouteRequirement {
  /** The matched sidebar prefix (longest match wins). */
  prefix: string;
  /** Single required permission (optional). */
  permission?: string;
  /** Alternative permissions — any one grants access. */
  anyOf?: string[];
}

interface Candidate {
  prefix: string;
  permission?: string;
  anyOf?: string[];
}

const CANDIDATES: Candidate[] = ADMIN_NAV.flatMap((group) =>
  group.items.map((item) => ({
    prefix: item.href,
    permission: item.permission,
    anyOf: item.anyOf,
  }))
)
  // Longest prefix first so `/admin/reports` beats `/admin`.
  .sort((a, b) => b.prefix.length - a.prefix.length);

function matches(prefix: string, pathname: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

/** Requirement for a pathname, or `null` when the route is not permission-gated. */
export function requiredPermissionFor(pathname: string): RouteRequirement | null {
  const match = CANDIDATES.find((candidate) => matches(candidate.prefix, pathname));
  if (!match) return null;
  const { prefix, permission, anyOf } = match;
  if (!permission && (!anyOf || anyOf.length === 0)) return { prefix };
  return { prefix, permission, anyOf };
}

/** True when `permissions` satisfies the requirement for `pathname`. */
export function canAccessPath(
  pathname: string,
  permissions: string[] | undefined | null
): boolean {
  const requirement = requiredPermissionFor(pathname);
  if (!requirement) return true;
  const codes = [
    ...(requirement.permission ? [requirement.permission] : []),
    ...(requirement.anyOf ?? []),
  ];
  if (codes.length === 0) return true;
  return hasAnyPermission(permissions, codes);
}
