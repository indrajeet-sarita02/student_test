// Sidebar navigation. `permission` (when set) filters the item by RBAC.

export interface NavItem {
  href: string;
  label: string;
  icon: string; // emoji keeps the bundle tiny; swap for an icon lib later
  permission?: string;
  anyOf?: string[];
}

export interface NavGroup {
  section: string;
  items: NavItem[];
}

export const ADMIN_NAV: NavGroup[] = [
  {
    section: "Overview",
    items: [
      { href: "/admin", label: "Dashboard", icon: "📊", permission: "report.view" },
      { href: "/admin/reports", label: "Reports", icon: "📈", permission: "report.view" },
    ],
  },
  {
    section: "Content",
    items: [
      { href: "/admin/exams", label: "Exams", icon: "🎓", permission: "exam.view" },
      { href: "/admin/subjects", label: "Subjects", icon: "📚", permission: "exam.view" },
      { href: "/admin/topics", label: "Topics", icon: "🗂️", permission: "exam.view" },
      { href: "/admin/questions", label: "Questions", icon: "❓", permission: "question.view" },
      { href: "/admin/tests", label: "Tests", icon: "🧪", permission: "test.view" },
      { href: "/admin/assignments", label: "Assignments", icon: "📝", permission: "test.assign" },
    ],
  },
  {
    section: "Evaluation",
    items: [
      { href: "/admin/attempts", label: "Attempts", icon: "⏱️", permission: "attempt.view" },
      { href: "/admin/results", label: "Results", icon: "🏆", permission: "result.view" },
    ],
  },
  {
    section: "Administration",
    items: [
      { href: "/admin/users", label: "Users", icon: "👥", permission: "user.view" },
      { href: "/admin/roles", label: "Roles", icon: "🛡️", permission: "role.view" },
      { href: "/admin/permissions", label: "Permissions", icon: "🔑", permission: "permission.view" },
      { href: "/admin/notifications", label: "Notifications", icon: "🔔", permission: "notification.view" },
      { href: "/admin/audit-logs", label: "Audit Logs", icon: "📜", permission: "audit.view" },
      { href: "/admin/settings", label: "Settings", icon: "⚙️", permission: "settings.view" },
    ],
  },
  {
    section: "Account",
    items: [{ href: "/admin/profile", label: "Profile", icon: "👤" }],
  },
];

export const MAIN_NAV: NavGroup[] = [
  {
    section: "Main",
    items: [
      { href: "/", label: "Home", icon: "🏠" },
      { href: "/tests", label: "Available Tests", icon: "🧪" },
      { href: "/history", label: "My Attempts", icon: "⏱️" },
      { href: "/results", label: "My Results", icon: "🏆" },
      { href: "/notifications", label: "Notifications", icon: "🔔" },
      { href: "/profile", label: "Profile", icon: "👤" },
    ],
  },
];
