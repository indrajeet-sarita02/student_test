// RBAC helpers. The backend is authoritative; these only drive UI visibility
// and route guards. SUPER_ADMIN is represented by the "*" permission.

export const SUPER_PERMISSION = "*";

export const ADMIN_ROLES = [
  "SUPER_ADMIN",
  "ADMIN",
  "CONTENT_MANAGER",
  "EXAMINER",
  "REPORT_VIEWER",
];

export function hasPermission(
  permissions: string[] | undefined | null,
  code: string
): boolean {
  if (!permissions || permissions.length === 0) return false;
  if (permissions.includes(SUPER_PERMISSION)) return true;
  return permissions.includes(code);
}

export function hasAnyPermission(
  permissions: string[] | undefined | null,
  codes: string[]
): boolean {
  return codes.some((code) => hasPermission(permissions, code));
}

export function isStaff(roleCodes: string[] | undefined | null): boolean {
  if (!roleCodes) return false;
  return roleCodes.some((code) => ADMIN_ROLES.includes(code));
}

/** Where to land after login based on role. */
export function landingPathFor(roleCodes: string[] | undefined | null): string {
  return isStaff(roleCodes) ? "/admin" : "/";
}
