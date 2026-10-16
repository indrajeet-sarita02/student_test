"use client";

import Link from "next/link";

import { reportsApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import { formatPercent } from "@/lib/utils";
import {
  Alert,
  Card,
  CardBody,
  CardHeader,
  LoadingBlock,
  PageHeader,
  StatCard,
} from "@/components/ui";

export default function AdminDashboardPage() {
  const report = useApi(() => reportsApi.dashboard());

  const d = report.data;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="A snapshot of platform activity."
        actions={
          <Link
            href="/admin/reports"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            View reports
          </Link>
        }
      />

      {report.loading ? (
        <LoadingBlock />
      ) : report.error ? (
        <Alert tone="error">{report.error}</Alert>
      ) : !d ? null : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            <StatCard label="Students" value={d.total_students} icon="🎓" hint={`${d.total_users} users total`} />
            <StatCard label="Exams" value={d.total_exams} icon="📘" />
            <StatCard label="Tests" value={d.total_tests} icon="🧪" hint={`${d.published_tests} published`} />
            <StatCard label="Questions" value={d.total_questions} icon="❓" />
          </div>

          <div className="mt-3 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            <StatCard label="Attempts" value={d.total_attempts} icon="⏱️" hint={`${d.active_attempts} active`} />
            <StatCard label="Results" value={d.total_results} icon="🏆" />
            <StatCard label="Avg percentage" value={formatPercent(d.average_percentage)} icon="📈" />
            <StatCard label="Pass rate" value={formatPercent(d.pass_rate)} icon="✅" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <QuickLinkCard
              title="Manage users"
              description="Create users, assign roles and control access."
              href="/admin/users"
              icon="👥"
            />
            <QuickLinkCard
              title="Author questions"
              description="Add questions and organise them by subject and topic."
              href="/admin/questions"
              icon="❓"
            />
            <QuickLinkCard
              title="Build tests"
              description="Assemble tests, attach questions and publish."
              href="/admin/tests"
              icon="🧪"
            />
          </div>
        </>
      )}
    </div>
  );
}

function QuickLinkCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
}) {
  return (
    <Link href={href}>
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardBody>
          <div className="mb-2 text-2xl">{icon}</div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-0.5 text-xs text-slate-500">{description}</p>
        </CardBody>
      </Card>
    </Link>
  );
}
