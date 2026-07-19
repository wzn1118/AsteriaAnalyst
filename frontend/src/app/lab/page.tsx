import { Suspense } from "react";

import { AnalysisWorkspaceShell } from "@/components/analysis-workspace-shell";

export default function LabPage() {
  return (
    <main className="min-h-dvh w-full overflow-auto bg-[#050806] text-white xl:h-dvh xl:overflow-hidden">
      <Suspense fallback={null}>
        <AnalysisWorkspaceShell />
      </Suspense>
    </main>
  );
}
