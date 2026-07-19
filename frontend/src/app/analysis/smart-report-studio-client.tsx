"use client";

import dynamic from "next/dynamic";

const SmartReportStudio = dynamic(
  () => import("@/components/smart-report-studio").then((module) => module.SmartReportStudio),
  { ssr: false },
);

export function SmartReportStudioClient() {
  return <SmartReportStudio />;
}
