"use client";

import { useRouter } from "next/navigation";

import { ReportRevisionWorkbench } from "@/components/report-revision-workbench";

export function RevisionModeShell() {
  const router = useRouter();

  return <ReportRevisionWorkbench backHref="/" onBack={() => router.push("/")} workspaceMode="library" />;
}
