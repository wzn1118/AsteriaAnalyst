"use client";

import { useSearchParams } from "next/navigation";

import { ReportRevisionWorkbench } from "@/components/report-revision-workbench";

export function RevisionWorkspaceShell() {
  const searchParams = useSearchParams();
  const reportId = searchParams.get("report_id") || "";
  const sessionId = searchParams.get("session_id") || "";

  return (
    <ReportRevisionWorkbench
      backHref="/revision"
      initialReportId={reportId}
      initialSessionId={sessionId}
      workspaceMode="session"
    />
  );
}
