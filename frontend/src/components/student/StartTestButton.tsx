"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { studentApi } from "@/lib/api/endpoints";
import { isApiError } from "@/lib/api/client";
import { useToast } from "@/components/Toast";
import { Button } from "@/components/ui";

export function StartTestButton({
  testId,
  label = "Start test",
  size = "sm",
  variant = "primary",
}: {
  testId: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "outline" | "success";
}) {
  const router = useRouter();
  const toast = useToast();
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    try {
      const res = await studentApi.start(testId);
      router.push(`/attempts/${res.attempt.id}`);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Unable to start the test.");
      setLoading(false);
    }
  };

  return (
    <Button size={size} variant={variant} loading={loading} onClick={start}>
      {label}
    </Button>
  );
}
