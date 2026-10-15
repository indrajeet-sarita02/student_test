"use client";

import Link from "next/link";

import { examsApi, questionsApi, usersApi } from "@/lib/api/endpoints";
import { useApi } from "@/lib/hooks";
import {
  Alert,
  Card,
  CardBody,
  LoadingBlock,
  PageHeader,
  StatCard,
} from "@/components/ui";

export default function AdminDashboardPage() {
  const stats = useApi(async () => {
    const [users, exams, questions] = await Promise.all([
      usersApi.list({ page: 1, page_size: 1 }),
      examsApi.list({ page: 1, page_size: 1 }),
      questionsApi.list({ page: 1, page_size: 1 }),
    ]);
    return {
      totalUsers: users.total,
      totalExams: exams.total,
      totalQuestions: questions.total,
    };
  });

  const d = stats.data;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="A snapshot of platform activity."
      />

      {stats.loading ? (
        <LoadingBlock />
      ) : stats.error ? (
        <Alert tone="error">{stats.error}</Alert>
      ) : !d ? null : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
            <StatCard label="Users" value={d.totalUsers} icon="👥" />
            <StatCard label="Exams" value={d.totalExams} icon="📘" />
            <StatCard label="Questions" value={d.totalQuestions} icon="❓" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <QuickLinkCard
              title="Manage users"
              description="Create users, assign roles and control access."
              href="/admin/users"
              icon="👥"
            />
            <QuickLinkCard
              title="Manage exams"
              description="Create exams, subjects and topics."
              href="/admin/exams"
              icon="🎓"
            />
            <QuickLinkCard
              title="Author questions"
              description="Add questions and organise them by subject and topic."
              href="/admin/questions"
              icon="❓"
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
