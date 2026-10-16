"use client";

import { RequireAuth } from "@/components/guards";

export default function AttemptLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
